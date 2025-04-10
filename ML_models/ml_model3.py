import pandas as pd
import os
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import joblib

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
    print(f"Bike data shape before cleaning: {bike_df.shape}")
    bike_df = bike_df.dropna(subset=['timestamp']).copy()
    weather_df = weather_df.dropna(subset=['timestamp']).copy()
    print(f"Bike data shape after cleaning: {bike_df.shape}")
    print(f"Weather data shape after cleaning: {weather_df.shape}")

    bike_df['timestamp'] = bike_df['timestamp'].dt.round('H')
    weather_df['timestamp'] = weather_df['timestamp'].dt.round('H')

    bike_df.sort_values('timestamp', inplace=True)
    weather_df.sort_values('timestamp', inplace=True)

    # Merge Bike and Weather Data
    merged_df = pd.merge_asof(bike_df, weather_df, on='timestamp', direction='nearest')
    columns_to_drop = ['status', 'weather_id', 'city_id']
    merged_df.drop(columns=[col for col in columns_to_drop if col in merged_df.columns], inplace=True)
    print(f"Merge successful! Merged data shape: {merged_df.shape}")

    # Feature Engineering
    merged_df['hour'] = merged_df['timestamp'].dt.hour
    merged_df['day_of_week'] = merged_df['timestamp'].dt.dayofweek
    merged_df['is_weekend'] = merged_df['day_of_week'].isin([5, 6]).astype(int)
    merged_df['month'] = merged_df['timestamp'].dt.month
  
    
    # Target Variable
    merged_df['target'] = merged_df['available_bikes']

    merged_df.dropna(inplace=True)

    if 'number' in merged_df.columns:
        features = ['hour', 'day_of_week', 'is_weekend', 'month', 'number']
    else:
        print("Warning: 'number' column not found. Proceeding without it.")
        features = ['hour', 'day_of_week', 'is_weekend', 'month']

    X = merged_df[features]
    y = merged_df['target']

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=True, test_size=0.2, random_state=42)

    # Train XGBoost model
    xgb_model = XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42)
    xgb_model.fit(X_train, y_train)

    # Evaluate model
    preds = xgb_model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    print(f"XGBoost MAE: {mae:.2f}")

    # Save model
    joblib.dump(xgb_model, 'bike_forecast_xgb.pkl')
    print("Model saved as 'bike_forecast_xgb.pkl'")
else:
    print("Error: 'timestamp' column missing in one or both datasets.")

