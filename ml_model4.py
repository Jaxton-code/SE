import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from sklearn.cluster import KMeans
import joblib
import os

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

    # Save merged dataset for reuse or inspection
    merged_df.to_csv("merged_bike_weather_data.csv", index=False)
    print("Merged dataset saved to 'merged_bike_weather_data.csv'")

    #add in lat and long for clustering this has helped create a better model as I can instead of creating a singlular model with high MAE or a model per station i group by coordinates and create a few models
    station_info = pd.read_csv("/Users/shaneobrien/desktop/SE/station_info.csv")
    merged_df = pd.merge(merged_df, station_info[['number', 'latitude', 'longitude']], on='number', how='left')
    print("Added station latitude and longitude.")


    # Feature Engineering
    merged_df['hour'] = merged_df['timestamp'].dt.hour
    merged_df['day_of_week'] = merged_df['timestamp'].dt.dayofweek
    merged_df['is_weekend'] = merged_df['day_of_week'].isin([5, 6]).astype(int)
    merged_df['month'] = merged_df['timestamp'].dt.month

    # Cluster stations by latitude/longitude (assuming columns exist)
    if {'number', 'latitude', 'longitude'}.issubset(merged_df.columns):
        station_coords = merged_df.groupby('number')[['latitude', 'longitude']].mean().reset_index()
        kmeans = KMeans(n_clusters=5, random_state=42)
        station_coords['cluster'] = kmeans.fit_predict(station_coords[['latitude', 'longitude']])
        cluster_map = station_coords.set_index('number')['cluster'].to_dict()
        merged_df['cluster'] = merged_df['number'].map(cluster_map)

        os.makedirs("models_per_cluster", exist_ok=True)

        for cluster_id in sorted(merged_df['cluster'].unique()):
            cluster_df = merged_df[merged_df['cluster'] == cluster_id].copy()
            cluster_df.dropna(inplace=True)

            features = ['hour', 'day_of_week', 'is_weekend', 'month', 'temperature', 'wind']
            if 'number' in cluster_df.columns:
                features.append('number')

            X = cluster_df[features]
            y = cluster_df['available_bikes']

            X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=True, test_size=0.2, random_state=42)

            xgb_model = XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42)
            xgb_model.fit(X_train, y_train)

            preds = xgb_model.predict(X_test)
            mae = mean_absolute_error(y_test, preds)
            print(f"Cluster {cluster_id} MAE: {mae:.2f}")
            joblib.dump({'model': xgb_model, 'features': features}, f'models_per_cluster/cluster_{cluster_id}.pkl')

    else:
        print("Missing 'latitude' or 'longitude' in merged data. Cannot perform clustering.")

else:
    print("Error: 'timestamp' column missing in one or both datasets.")
