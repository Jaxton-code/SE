import pandas as pd
import joblib
import matplotlib.pyplot as plt
import os
import json

# Load Merged Data
merged_df = pd.read_csv("merged_bike_weather_data.csv")

merged_df['number'] = merged_df['number'].astype(int)
# Load cluster map
with open("models_per_cluster/station_cluster_map.json", "r") as f:
    cluster_map = json.load(f)
cluster_map = {int(k): v for k, v in cluster_map.items()}


# Assign clusters to data
merged_df['cluster'] = merged_df['number'].map(cluster_map)
merged_df.dropna(subset=['cluster'], inplace=True)

# Fix dtype issue
merged_df['number'] = merged_df['number'].astype(int)
cluster_map = {int(k): v for k, v in cluster_map.items()}
merged_df['cluster'] = merged_df['number'].map(cluster_map)

# Check if any clusters were assigned
clusters = sorted(merged_df['cluster'].dropna().unique())
n_clusters = len(clusters)

if n_clusters == 0:
    raise ValueError("No clusters found in merged_df — check if cluster_map matches 'number' type.")


# For consistency with training
merged_df['timestamp'] = pd.to_datetime(merged_df['timestamp'], format='mixed', errors='coerce')

merged_df = merged_df.sort_values(['number', 'timestamp'])

# Recreate lag features to match training
# merged_df['lag_1'] = merged_df.groupby('number')['available_bikes'].shift(1)
# merged_df['lag_2'] = merged_df.groupby('number')['available_bikes'].shift(2)
# merged_df['lag_3'] = merged_df.groupby('number')['available_bikes'].shift(3)


# Optional: sort by timestamp again
merged_df.sort_values('timestamp', inplace=True)

# Features to use (must match model)
base_features = ['hour', 'day_of_week', 'is_weekend', 'month', 'temperature', 'wind', 
                 'is_peak_morning', 'is_peak_evening', 'weather_code',
                 'station_bike_capacity', 'station_mean_bikes', 'station_std_bikes',
                  'number']

# Create plot
clusters = sorted(merged_df['cluster'].unique())
n_clusters = len(clusters)
cols = 2
rows = (n_clusters + 1) // cols

fig, axes = plt.subplots(rows, cols, figsize=(14, 4 * rows))
axes = axes.flatten()

for i, cluster_id in enumerate(clusters):
    print(f"Processing cluster {cluster_id}")
    model_path = f"models_per_cluster/cluster_{cluster_id}.pkl"

    if not os.path.exists(model_path):
        print(f"Model for cluster {cluster_id} not found.")
        continue

    # Load model
    model_bundle = joblib.load(model_path)
    model = model_bundle['model']
    features = model_bundle['features']

    cluster_df = merged_df[merged_df['cluster'] == cluster_id].copy()
    cluster_df.dropna(subset=features + ['available_bikes'], inplace=True)

    # Time-based split
    split_idx = int(len(cluster_df) * 0.8)
    test_df = cluster_df.iloc[split_idx:]

    X_test = test_df[features]
    y_test = test_df['available_bikes']
    preds = model.predict(X_test)

        # Store predictions alongside timestamps
    test_df = test_df.copy()
    test_df['predicted'] = preds
    test_df['actual'] = y_test.values

    # Combine and average over timestamps to smooth across stations
    combined = test_df[['timestamp', 'actual', 'predicted']]
    grouped = combined.groupby('timestamp').mean().reset_index()

    #rolling average for visual smoothing
    grouped['actual_smooth'] = grouped['actual'].rolling(3).mean()
    grouped['predicted_smooth'] = grouped['predicted'].rolling(3).mean()

    # Plot
    ax = axes[i]
    ax.plot(grouped['timestamp'], grouped['actual_smooth'], label='Actual', alpha=0.8)
    ax.plot(grouped['timestamp'], grouped['predicted_smooth'], label='Predicted', alpha=0.8)
    ax.set_title(f"Cluster {cluster_id}")
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Available Bikes")
    ax.legend()


# Remove extra empty plots
for j in range(i + 1, len(axes)):
    fig.delaxes(axes[j])

fig.tight_layout()
plt.suptitle("Predicted vs Actual Bike Availability per Cluster", fontsize=16, y=1.02)
plt.show()
