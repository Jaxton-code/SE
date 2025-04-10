import os
import pandas as pd
import matplotlib.pyplot as plt

# Setup
results_dir = "models_per_cluster"
cluster_data = {}

# Collect data from all CSVs
for filename in os.listdir(results_dir):
    if filename.startswith("high_error_cluster_") and filename.endswith(".csv"):
        cluster_id = filename.split("_")[-1].replace(".csv", "")
        filepath = os.path.join(results_dir, filename)
        df = pd.read_csv(filepath)
        if {'actual', 'predicted'}.issubset(df.columns):
            cluster_data[cluster_id] = df

# Sort clusters numerically
cluster_ids = sorted(cluster_data.keys(), key=int)
n_clusters = len(cluster_ids)

# Plot setup (auto grid size)
cols = 2
rows = (n_clusters + 1) // cols

fig, axes = plt.subplots(rows, cols, figsize=(14, 4 * rows))
axes = axes.flatten()

# Plot each cluster
for idx, cluster_id in enumerate(cluster_ids):
    df = cluster_data[cluster_id]
    ax = axes[idx]
    ax.plot(df['actual'].values[:100], label='Actual', marker='o')
    ax.plot(df['predicted'].values[:100], label='Predicted', marker='x')
    ax.set_title(f'Cluster {cluster_id}')
    ax.set_xlabel("Sample Index")
    ax.set_ylabel("Available Bikes")
    ax.legend()
    ax.grid(True)

# Remove any empty subplots
for j in range(len(cluster_ids), len(axes)):
    fig.delaxes(axes[j])

fig.suptitle("Model 4 - Predicted vs Actual (All Clusters)", fontsize=16)
plt.tight_layout(rect=[0, 0.03, 1, 0.97])
plt.savefig("model4_all_clusters_combined.png")
plt.show()
