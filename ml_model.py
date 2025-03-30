import pandas as pd
import os
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
            # Use explicit format instead of relying on pandas inference
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
            # Use format parameter instead of dayfirst
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
    
    # Ensure timestamp types match exactly
    bike_df['timestamp'] = pd.to_datetime(bike_df['timestamp'])
    weather_df['timestamp'] = pd.to_datetime(weather_df['timestamp'])
    
    print(f"Bike timestamp dtype: {bike_df['timestamp'].dtype}")
    print(f"Weather timestamp dtype: {weather_df['timestamp'].dtype}")
    
    bike_df.sort_values('timestamp', inplace=True)
    weather_df.sort_values('timestamp', inplace=True)
    
    # Merge Bike and Weather Data (Nearest Timestamp)
    try:
        merged_df = pd.merge_asof(
            bike_df,
            weather_df,
            on='timestamp',
            direction='nearest'
        )
        print(f"Merge successful! Merged data shape: {merged_df.shape}")
    except Exception as e:
        print(f"Merge failed with error: {e}")
        # Try a more stringent approach if the first merge fails
        print("Trying alternative approach...")
        # Convert to unix timestamp (this sometimes helps with merge_asof issues)
        bike_df['timestamp_unix'] = bike_df['timestamp'].astype(int) // 10**9
        weather_df['timestamp_unix'] = weather_df['timestamp'].astype(int) // 10**9
        
        bike_df = bike_df.sort_values('timestamp_unix')
        weather_df = weather_df.sort_values('timestamp_unix')
        
        merged_df = pd.merge_asof(
            bike_df,
            weather_df,
            on='timestamp_unix',
            direction='nearest'
        )
        print(f"Alternative merge successful! Merged data shape: {merged_df.shape}")
    
    # Rest of code remains the same
    # Feature Engineering
    merged_df['hour'] = merged_df['timestamp'].dt.hour
    merged_df['day_of_week'] = merged_df['timestamp'].dt.dayofweek
    merged_df['is_weekend'] = merged_df['day_of_week'].isin([5, 6]).astype(int)
    
    # Target Variable (Predict Next Snapshot of Available Bikes)
    merged_df['target'] = merged_df['available_bikes'].shift(-1)
    
    # Drop Rows with Missing Target
    merged_df.dropna(inplace=True)
    
    # Define Features and Labels
    # Ensure 'number' column is in the merged dataset
    if 'number' in merged_df.columns:
        # Add 'number' to the feature list
        features = ['hour', 'day_of_week', 'is_weekend', 'temperature', 'wind', 'number']
    else:
        print("⚠️ Warning: 'number' column not found. Proceeding without it.")
        features = ['hour', 'day_of_week', 'is_weekend', 'temperature', 'wind']

    # Define Features (X) and Target (y)
    X = merged_df[features]
    y = merged_df['target']

    
    # Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=False, test_size=0.2)
    
    
# Define parameter grid
param_grid = {
    'n_estimators': [50, 100, 200],   # Number of trees
    'max_depth': [5, 10, 20],         # Depth of each tree
    'min_samples_split': [2, 5, 10],  # Minimum samples to split
    'min_samples_leaf': [1, 2, 4]     # Minimum samples per leaf
}

# Run Randomized Search
rf_random = RandomizedSearchCV(
    RandomForestRegressor(),
    param_distributions=param_grid,
    n_iter=10, cv=3, scoring='neg_mean_absolute_error', n_jobs=-1
)

rf_random.fit(X_train, y_train)

# Use the best model found
best_model = rf_random.best_estimator_

# Make Predictions and Evaluate
preds = best_model.predict(X_test)
mae = mean_absolute_error(y_test, preds)

# Output Results
print("Optimized MAE:", mae)
print("Best Hyperparameters:", rf_random.best_params_)
   