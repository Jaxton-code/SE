import pandas as pd
import json
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# Load dataset
df = pd.read_csv("merged_bike_weather_data.csv")

# Ensure datetime format
df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
df['hour'] = df['timestamp'].dt.hour
df['day_of_week'] = df['timestamp'].dt.dayofweek
df = df.dropna(subset=['hour', 'day_of_week', 'available_bikes'])

# Compute avg_bikes_hour_dow
avg_usage = (
    df.groupby(['number', 'hour', 'day_of_week'])['available_bikes']
    .mean()
    .reset_index()
    .rename(columns={'available_bikes': 'avg_bikes_hour_dow'})
)
df = pd.merge(df, avg_usage, on=['number', 'hour', 'day_of_week'], how='left')

# Time usage clustering
station_hourly = (
    df.groupby(['number', 'hour'])['available_bikes']
    .mean()
    .unstack(fill_value=0)
)

scaled = StandardScaler().fit_transform(station_hourly)
kmeans = KMeans(n_clusters=15, random_state=42)
station_hourly['time_cluster'] = kmeans.fit_predict(scaled)

# Merge time_cluster back
cluster_map = station_hourly['time_cluster'].to_dict()
df['time_cluster'] = df['number'].map(cluster_map)

# Drop rows without all required columns
required = [
    'station_bike_capacity', 'station_mean_bikes', 'station_std_bikes',
    'avg_bikes_hour_dow', 'time_cluster'
]
df = df.dropna(subset=required)

# Build metadata
metadata = {}

# Grouped hourly averages
grouped = df.groupby(['number', 'hour', 'day_of_week'])['avg_bikes_hour_dow'].mean()

for station in df['number'].unique():
    station_df = df[df['number'] == station]
    if station_df.empty:
        continue
    latest = station_df.iloc[-1]

    metadata[int(station)] = {
        "station_bike_capacity": int(latest['station_bike_capacity']),
        "station_mean_bikes": float(latest['station_mean_bikes']),
        "station_std_bikes": float(latest['station_std_bikes']),
        "time_cluster": int(latest['time_cluster']),
        "hourly_avg": {}
    }

    for (s, h, dow), val in grouped.items():
        if s == station:
            metadata[int(station)]['hourly_avg'][f"{h}_{dow}"] = float(val)

# Save
with open("station_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print(" station_metadata.json created successfully.")
