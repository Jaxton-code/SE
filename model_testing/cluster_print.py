import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error

# Load dataset
merged_df = pd.read_csv("merged_bike_weather_data.csv", parse_dates=['timestamp'])

# Load time cluster map
with open("models_per_cluster/time_usage_cluster_map.json", "r") as f:
    time_cluster_map = json.load(f)
time_cluster_map = {int(k): v for k, v in time_cluster_map.items()}
merged_df['time_cluster'] = merged_df['number'].map(time_cluster_map)

# Recreate avg_bikes_hour_dow
merged_df['timestamp'] = pd.to_datetime(merged_df['timestamp'], errors='coerce')

merged_df['hour'] = merged_df['timestamp'].dt.hour
merged_df['day_of_week'] = merged_df['timestamp'].dt.dayofweek

avg_usage = (
    merged_df.groupby(['number', 'hour', 'day_of_week'])['available_bikes']
    .mean()
    .reset_index()
    .rename(columns={'available_bikes': 'avg_bikes_hour_dow'})
)

merged_df = pd.merge(
    merged_df,
    avg_usage,
    on=['number', 'hour', 'day_of_week'],
    how='left'
)

# Evaluate each cluster
results = []
for cluster_id in sorted(merged_df['time_cluster'].unique()):
    model_path = f"models_per_cluster/cluster_{cluster_id}.pkl"
    if not os.path.exists(model_path):
        print(f"Missing model for cluster {cluster_id}")
        continue

    model_bundle = joblib.load(model_path)
    model = model_bundle['model']
    features = [f for f in model_bundle['features'] if f in merged_df.columns]

    df = merged_df[merged_df['time_cluster'] == cluster_id].copy()
    df.dropna(subset=features + ['available_bikes'], inplace=True)
    df = df.sort_values('timestamp')

    X = df[features]
    y = df['available_bikes']
    split_idx = int(len(X) * 0.8)
    X_test, y_test = X.iloc[split_idx:], y.iloc[split_idx:]

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)

    results.append({'Cluster': cluster_id, 'Average MAE': round(mae, 2)})

# Output results
mae_df = pd.DataFrame(results)
print("\n=== Average MAE by Cluster ===")
print(mae_df.to_string(index=False))
