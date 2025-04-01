import pandas as pd
import os
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import RandomizedSearchCV

# Define Directories
bike_dir = "/Users/shaneobrien/desktop/bike_data"
weather_dir = "/Users/shaneobrien/desktop/weather_data"

# Load and Process Bike Data
bike_files = [os.path.join(bike_dir, f) for f in os.listdir(bike_dir) if f.endswith('.csv')]
bike_list = []

for file in bike_files:
    try:
        df = pd.read_csv(file)
        if not df.empty and 'last_update' in df.columns:
            df.rename(columns={'last_update': 'timestamp'}, inplace=True)
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
            bike_list.append(df)
    except Exception as e:
        print(f"Error processing bike file {file}: {e}")

bike_df = pd.concat(bike_list, ignore_index=True) if bike_list else pd.DataFrame()

# Load and Process Weather Data
weather_files = [os.path.join(weather_dir, f) for f in os.listdir(weather_dir) if f.endswith('.csv')]
weather_list = []

for file in weather_files:
    try:
        df = pd.read_csv(file)
        if not df.empty and 'create_time' in df.columns:
            df.rename(columns={
                'create_time': 'timestamp',
                'temp': 'temperature',
                'wind_speed': 'wind'
            }, inplace=True)
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
            weather_list.append(df)
    except Exception as e:
        print(f"Error processing weather file {file}: {e}")

weather_df = pd.concat(weather_list, ignore_index=True) if weather_list else pd.DataFrame()

# Ensure Data is Sorted for Merge
if 'timestamp' in bike_df.columns and 'timestamp' in weather_df.columns:
    # Debug info
    print(f"Bike data shape before cleaning: {bike_df.shape}")
    print(f"Bike data null timestamps before cleaning: {bike_df['timestamp'].isna().sum()}")
    
    # Remove null timestamps before sorting and merging
    bike_df = bike_df.dropna(subset=['timestamp']).copy()
    weather_df = weather_df.dropna(subset=['timestamp']).copy()
    
    # Debug info
    print(f"Bike data shape after cleaning: {bike_df.shape}")
    print(f"Bike data null timestamps after cleaning: {bike_df['timestamp'].isna().sum()}")
    print(f"Weather data shape after cleaning: {weather_df.shape}")
    print(f"Weather data null timestamps after cleaning: {weather_df['timestamp'].isna().sum()}")
    
    #round up to remove noise in attempt to get better MAE
    bike_df['timestamp'] = bike_df['timestamp'].dt.round('H')
    weather_df['timestamp'] = weather_df['timestamp'].dt.round('H')

    # Ensure timestamp types match exactly
    bike_df['timestamp'] = pd.to_datetime(bike_df['timestamp'])
    weather_df['timestamp'] = pd.to_datetime(weather_df['timestamp'])
    
    bike_df.sort_values('timestamp', inplace=True)
    weather_df.sort_values('timestamp', inplace=True)
    
    # Merge Bike and Weather Data
    merged_df = pd.merge_asof(
        bike_df,
        weather_df,
        on='timestamp',
        direction='nearest'
    )
    columns_to_drop = ['status', 'weather_id', 'city_id']
    merged_df.drop(columns=[col for col in columns_to_drop if col in merged_df.columns], inplace=True)
    print(f"Final dataset size after lag/target processing: {merged_df.shape}")



    print(f"Merge successful! Merged data shape: {merged_df.shape}")
    
    # Feature Engineering
    merged_df['hour'] = merged_df['timestamp'].dt.hour
    merged_df['day_of_week'] = merged_df['timestamp'].dt.dayofweek
    merged_df['is_weekend'] = merged_df['day_of_week'].isin([5, 6]).astype(int)
    merged_df['lag_1'] = merged_df['available_bikes'].shift(1)
    merged_df['lag_2'] = merged_df['available_bikes'].shift(2)
    merged_df['is_rush_hour'] = merged_df['hour'].isin([7, 8, 9, 17, 18]).astype(int)
    merged_df['rolling_bikes'] = merged_df['available_bikes'].rolling(window=3).mean().shift(1)




   

    
    # Target Variable (Predict Next Snapshot of Available Bikes)
    merged_df['target'] = merged_df['available_bikes']
    
    # Drop Rows with Missing Target
    merged_df.dropna(inplace=True)
    
    # Define Features and Labels
    
    if 'number' in merged_df.columns:
        features = [
            'hour', 'day_of_week', 'is_weekend', 'temperature', 'wind', 'number',
            'lag_1', 'lag_2', 'is_rush_hour', 'rolling_bikes'
        ]
    else:
        print("Warning: 'number' column not found. Proceeding without it.")
        features = [
            'hour', 'day_of_week', 'is_weekend', 'temperature', 'wind',
            'lag_1', 'lag_2', 'is_rush_hour', 'rolling_bikes'
        ]





    # STAGE 1: TUNING WITH SAMPLE
    print("\n=== STAGE 1: Hyperparameter Tuning with Sample ===")
    # Create a smaller sample for hyperparameter tuning
    sample_size = 200000  # Adjust based  computational resources
    print(f"Creating sample of {sample_size} rows for hyperparameter tuning")
    merged_df_sample = merged_df.sample(n=sample_size, random_state=42)
    
    # Prepare sample data
    X_sample = merged_df_sample[features]
    y_sample = merged_df_sample['target']
    
    # Split the sample
    X_train_sample, X_test_sample, y_train_sample, y_test_sample = train_test_split(
        X_sample, y_sample, shuffle=False, test_size=0.2
    )
    
    # Define parameter grid
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [10, 20, 30],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4]
    }
    
    # Run Randomized Search on sample
    print("Starting hyperparameter search (this will be much faster on the sample)...")
    rf_random = RandomizedSearchCV(
        RandomForestRegressor(random_state=42),
        param_distributions=param_grid,
        n_iter=10, cv=3, scoring='neg_mean_absolute_error',
        n_jobs=-1, random_state=42
    )
    
    rf_random.fit(X_train_sample, y_train_sample)
    
    # Evaluate tuned model on sample test set
    best_sample_model = rf_random.best_estimator_
    sample_preds = best_sample_model.predict(X_test_sample)
    sample_mae = mean_absolute_error(y_test_sample, sample_preds)
    
    print(f"Sample model MAE: {sample_mae}")
    print(f"Best parameters found: {rf_random.best_params_}")
    
    # STAGE 2: TRAIN FULL MODEL WITH OPTIMAL PARAMETERS
    print("\n=== STAGE 2: Training on Full Dataset with Optimal Parameters ===")
    # Prepare full dataset
    X = merged_df[features]
    y = merged_df['target']
    
    # Split the full dataset
    X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=False, test_size=0.2)
    
    # Train model with best parameters from search
    print("Training final model on full dataset with optimal parameters...")
    final_model = RandomForestRegressor(**rf_random.best_params_, random_state=42)
    final_model.fit(X_train, y_train)
    
    # Evaluate on full test set
    full_preds = final_model.predict(X_test)
    full_mae = mean_absolute_error(y_test, full_preds)
    
    print(f"Final model MAE on full dataset: {full_mae}")
    
    # Feature importance analysis
    feature_importances = final_model.feature_importances_
    feature_importance_df = pd.DataFrame({
        'Feature': features,
        'Importance': feature_importances
    }).sort_values('Importance', ascending=False)
    
    print("\nFeature Importance:")
    print(feature_importance_df)
    
    # Option to save the model
    import joblib
    joblib.dump(final_model, 'bike_prediction_model.pkl')
    print("\nModel saved as 'bike_prediction_model.pkl'")
else:
    print(" Error: 'timestamp' column missing in one or both datasets.")