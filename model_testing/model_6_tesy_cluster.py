import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# === Step 1: Load Preprocessed Merged Data ===
merged_df = pd.read_csv("merged_bike_weather_data.csv")

# === Step 2: Create Station-Hourly Usage Matrix ===
station_hourly = (
    merged_df.groupby(['number', 'hour'])['available_bikes']
    .mean()
    .unstack(fill_value=0)
)

# === Step 3: Standardize the Data ===
scaler = StandardScaler()
X_scaled = scaler.fit_transform(station_hourly)

# === Step 4: Compute Inertia for Range of k ===
inertia = []
K = range(1, 30)  # Try up to 20 clusters

for k in K:
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(X_scaled)
    inertia.append(kmeans.inertia_)

# === Step 5: Plot the Elbow Curve ===
plt.figure(figsize=(8, 5))
plt.plot(K, inertia, 'bo-')
plt.xlabel('Number of Clusters (k)')
plt.ylabel('Inertia (Within-Cluster Sum of Squares)')
plt.title('Elbow Method for Optimal Temporal Clusters')
plt.grid(True)
plt.tight_layout()
plt.show()
