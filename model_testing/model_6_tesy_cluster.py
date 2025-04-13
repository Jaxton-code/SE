import os
import json
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error

# Load merged dataset
merged_df = pd.read_csv("merged_bike_weather_data.csv", parse_dates=['timestamp'])

# Load time-based cluster map
with open("models_per_cluster/time_usage_cluster_map.json", "r") as f:
    time_cluster_map = json.load(f)
time_cluster_map = {int(k): v for k, v in time_cluster_map.items()}
merged_df['time_cluster'] = merged_df['number'].map(time_cluster_map)



# Recompute avg_bikes_hour_dow
merged_df['timestamp'] = pd.to_datetime(merged_df['timestamp'], format='mixed', errors='coerce')
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

# Filter and clean
merged_df.dropna(inplace=True)

# Plot each cluster
for cluster_id in sorted(merged_df['time_cluster'].unique()):
    print(f"\nPlotting Actual vs Predicted for Cluster {cluster_id}...")

    model_path = f"models_per_cluster/cluster_{cluster_id}.pkl"
    if not os.path.exists(model_path):
        print(f"Model for Cluster {cluster_id} not found. Skipping.")
        continue

    model_bundle = joblib.load(model_path)
    model = model_bundle['model']
    features = model_bundle['features']

    cluster_df = merged_df[merged_df['time_cluster'] == cluster_id].copy()
    cluster_df = cluster_df.dropna(subset=features + ['available_bikes'])

    # Sort by time for consistent evaluation
    cluster_df = cluster_df.sort_values('timestamp')
    X = cluster_df[features]
    y = cluster_df['available_bikes']
    timestamps = cluster_df['timestamp']

    # Hold out final 20% for plotting
    split_idx = int(len(X) * 0.8)
    X_test = X.iloc[split_idx:]
    y_test = y.iloc[split_idx:]
    timestamps_test = timestamps.iloc[split_idx:]

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    print(f"MAE on test set: {mae:.2f}")

    # Plot
    plt.figure(figsize=(14, 5))
    plt.plot(timestamps_test, y_test.values, label='Actual', color='blue')
    plt.plot(timestamps_test, preds, label='Predicted', color='orange')
    plt.title(f'Cluster {cluster_id}: Actual vs Predicted Available Bikes')
    plt.xlabel('Timestamp')
    plt.ylabel('Available Bikes')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
