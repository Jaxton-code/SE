import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
from xgboost import XGBRegressor

from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import mean_absolute_error
from sklearn.cluster import KMeans
from sklearn.model_selection import TimeSeriesSplit
import joblib
import json


#NEW MODEL USING RANDOMISED SEARCH TO FIND BEST MODEL PARAMETERS 
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
                'wind_speed': 'wind',
                'temp_feel': 'temp_feel'
            }, inplace=True)
            
            weather_condition_map = {
                "Clear": 0, "Clouds": 1, "Mist": 2, "Drizzle": 3, "Rain": 4,
                 "Snow": 5, "Thunderstorm": 6, "Fog": 2}
            df['weather_code'] = df['weather_main'].map(weather_condition_map).fillna(-1).astype(int)




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
    merged_df['total_capacity'] = merged_df['available_bikes'] + merged_df['available_bike_stands']
    station_capacity = merged_df.groupby('number')['total_capacity'].max().reset_index()
    station_capacity.columns = ['number', 'station_bike_capacity']
    
    # Add station-level usage patterns
    usage_stats = merged_df.groupby('number')['available_bikes'].agg(['mean', 'std']).reset_index()
    usage_stats.columns = ['number', 'station_mean_bikes', 'station_std_bikes']
    merged_df = pd.merge(merged_df, usage_stats, on='number', how='left')

   

# Merge capacity back into the main dataset
    merged_df = pd.merge(merged_df, station_capacity, on='number', how='left')  
    columns_to_drop = ['status', 'weather_id', 'city_id']
    merged_df.drop(columns=[col for col in columns_to_drop if col in merged_df.columns], inplace=True)
    print(f"Merge successful! Merged data shape: {merged_df.shape}")
    merged_df.to_csv("merged_bike_weather_data.csv", index=False)



    # Add Station Coordinates
    station_info = pd.read_csv("/Users/shaneobrien/desktop/SE/station_info.csv")
    merged_df = pd.merge(merged_df, station_info[['number', 'latitude', 'longitude']], on='number', how='left')
    print("Added station latitude and longitude.")

    missing_coords = merged_df[['number', 'latitude', 'longitude']].isna().sum()
     # Check for missing lat/lng values after merge
    print("Missing coordinates after station merge:")
    print(missing_coords)

# Optional: show a few affected station numbers
    if missing_coords.any():
        print("Stations missing lat/lng:")
        print(merged_df[merged_df['latitude'].isna() | merged_df['longitude'].isna()]['number'].unique())



    # Feature Engineering
    merged_df['hour'] = merged_df['timestamp'].dt.hour
    merged_df['day_of_week'] = merged_df['timestamp'].dt.dayofweek
    merged_df['is_weekend'] = merged_df['day_of_week'].isin([5, 6]).astype(int)
    merged_df['is_peak_morning'] = merged_df['hour'].between(7, 10).astype(int)
    merged_df['is_peak_evening'] = merged_df['hour'].between(16, 19).astype(int)

    merged_df['month'] = merged_df['timestamp'].dt.month
    merged_df.to_csv("merged_bike_weather_data.csv", index=False)

    # avg_usage = (
    #     merged_df.groupby(['number', 'hour', 'day_of_week'])['available_bikes']
    #     .mean()
    #     .reset_index()
    #     .rename(columns={'available_bikes': 'avg_bikes_hour_dow'})
    # )

    merged_df['number'] = merged_df['number'].astype(int)
    station_info['number'] = station_info['number'].astype(int)


#     merged_df = pd.merge(
#     merged_df,
#     avg_usage,
#     on=['number', 'hour', 'day_of_week'],
#     how='left'
# )


    # merged_df['lag_1'] = merged_df.groupby('number')['available_bikes'].shift(1)
    # merged_df['lag_2'] = merged_df.groupby('number')['available_bikes'].shift(2)
    # merged_df['lag_3'] = merged_df.groupby('number')['available_bikes'].shift(3)

    # Cluster stations
    if {'number', 'latitude', 'longitude'}.issubset(merged_df.columns):
        station_coords = merged_df.groupby('number')[['latitude', 'longitude']].mean().reset_index()
        kmeans = KMeans(n_clusters=5, random_state=42)
        station_coords['cluster'] = kmeans.fit_predict(station_coords[['latitude', 'longitude']])
        cluster_map = station_coords.set_index('number')['cluster'].to_dict()
        merged_df['cluster'] = merged_df['number'].map(cluster_map)

        os.makedirs("models_per_cluster", exist_ok=True)
        with open("models_per_cluster/station_cluster_map.json", "w") as f:
            json.dump(cluster_map, f)
        print("Saved station → cluster mapping.")

        # Pivot to get average usage profile across hours for each station
    station_hourly = (
        merged_df.groupby(['number', 'hour'])['available_bikes']
        .mean()
        .unstack(fill_value=0)
    )

    # Normalize (optional, but helpful)
    from sklearn.preprocessing import StandardScaler
    scaled = StandardScaler().fit_transform(station_hourly)

    # Cluster
    # kmeans_time = KMeans(n_clusters=5, random_state=42)
    # station_hourly['time_cluster'] = kmeans_time.fit_predict(scaled)

    # Map cluster back to merged_df
    # time_cluster_map = station_hourly['time_cluster'].to_dict()
    # merged_df['time_cluster'] = merged_df['number'].map(time_cluster_map)

    # # Optional: save this mapping
    # import json
    # with open("models_per_cluster/time_usage_cluster_map.json", "w") as f:
    #     json.dump(time_cluster_map, f)


        # Hyperparameter Tuning Grid
    param_grid = {
            'n_estimators': [100, 200, 300],
            'max_depth': [3, 5, 6, 8],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'subsample': [0.6, 0.8, 1.0],
            'colsample_bytree': [0.6, 0.8, 1.0],
            'gamma': [0, 0.1, 0.3],
            'reg_alpha': [0, 0.1, 1],
            'reg_lambda': [1, 1.5, 2]
        }

    param_cache_path = "models_per_cluster/best_params.json"
    if os.path.exists(param_cache_path):
            with open(param_cache_path, "r") as f:
                best_params_dict = json.load(f)
    else:
            best_params_dict = {}

    for cluster_id in sorted(merged_df['cluster'].unique()):
            print(f"\n--- Training model for Cluster {cluster_id} ---")
            cluster_df = merged_df[merged_df['cluster'] == cluster_id].copy()
            cluster_df.dropna(inplace=True)

            features = ['hour', 'day_of_week', 'is_weekend', 'month', 'temperature', 'wind', 'is_peak_morning','is_peak_evening','weather_code','station_bike_capacity']
            features += ['station_mean_bikes', 'station_std_bikes']
            if 'number' in cluster_df.columns:
                features.append('number')

            X = cluster_df[features]
            y = cluster_df['available_bikes']

            split_idx = int(len(X) * 0.8)
            X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

           
            if str(cluster_id) in best_params_dict:
                print(f"Using cached hyperparameters for Cluster {cluster_id}")
                best_params = best_params_dict[str(cluster_id)]
            else:
                print(f"Tuning hyperparameters for Cluster {cluster_id}...")
                xgb_base = XGBRegressor(objective='reg:squarederror', random_state=42)
                search = RandomizedSearchCV(
                    estimator=xgb_base,
                    param_distributions=param_grid,
                    n_iter=25,
                    cv=3,
                    verbose=1,
                    n_jobs=-1,
                    scoring='neg_mean_absolute_error'
                )
                search.fit(X_train, y_train)
                best_params = search.best_params_
                best_params_dict[str(cluster_id)] = best_params

                with open(param_cache_path, "w") as f:
                    json.dump(best_params_dict, f, indent=2)

            xgb_model = XGBRegressor(**best_params, random_state=42)
            xgb_model.fit(X_train, y_train)

            preds = xgb_model.predict(X_test)
            mae = mean_absolute_error(y_test, preds)
            print(f"Cluster {cluster_id} MAE: {mae:.2f}")

            joblib.dump({'model': xgb_model, 'features': features}, f'models_per_cluster/cluster_{cluster_id}.pkl')

            errors = abs(preds - y_test)
            results_df = X_test.copy()
            results_df['actual'] = y_test.values
            results_df['predicted'] = preds
            results_df['error'] = errors
            high_error = results_df[results_df['error'] > 5]
            high_error.to_csv(f"models_per_cluster/high_error_cluster_{cluster_id}.csv", index=False)


else:
    print("Error: 'timestamp' column missing in one or both datasets.")
