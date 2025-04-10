import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error

# Load model
model = joblib.load('bike_prediction_model.pkl')

# Load the dataset
merged_df = pd.read_csv("merged_bike_weather_data.csv")


# Load station info and merge the 'number' column back if needed
station_info = pd.read_csv("/Users/shaneobrien/desktop/SE/station_info.csv")  # or wherever it's stored
if 'number' not in merged_df.columns:
    merged_df = pd.merge(merged_df, station_info[['address', 'number']], on='address', how='left')



# Convert timestamp back to datetime
merged_df['timestamp'] = pd.to_datetime(merged_df['timestamp'], format='mixed', errors='coerce')

merged_df.dropna(subset=['timestamp'], inplace=True)


# Recreate features
merged_df['hour'] = merged_df['timestamp'].dt.hour
merged_df['day_of_week'] = merged_df['timestamp'].dt.dayofweek
merged_df['is_weekend'] = merged_df['day_of_week'].isin([5, 6]).astype(int)
merged_df['lag_1'] = merged_df['available_bikes'].shift(1)
merged_df['lag_2'] = merged_df['available_bikes'].shift(2)
merged_df['is_rush_hour'] = merged_df['hour'].isin([7, 8, 9, 17, 18]).astype(int)
merged_df['rolling_bikes'] = merged_df['available_bikes'].rolling(window=3).mean().shift(1)

# Drop NaNs created by lag and rolling
merged_df.dropna(inplace=True)

# Select features
features = [
    'hour', 'day_of_week', 'is_weekend', 'temperature', 'wind',
    'lag_1', 'lag_2', 'is_rush_hour', 'rolling_bikes', 'number'
]
X = merged_df[features]
y = merged_df['available_bikes']

# Split test set (same as original)
split_idx = int(len(X) * 0.8)
X_test = X.iloc[split_idx:]
y_test = y.iloc[split_idx:]

expected_features = model.feature_names_in_
X_test = X_test[expected_features]

# Predict
preds = model.predict(X_test)

# Plot
plt.figure(figsize=(12, 6))
plt.plot(y_test.values[:100], label='Actual', marker='o')
plt.plot(preds[:100], label='Predicted', marker='x')
plt.title("ML Model 2 - Predicted vs Actual Bikes (First 100 samples)")
plt.xlabel("Sample Index")
plt.ylabel("Available Bikes")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("ml_model2_pred_vs_actual.png")
plt.show()

# Print MAE
mae = mean_absolute_error(y_test, preds)
print(f"Model 2 MAE: {mae:.2f}")
