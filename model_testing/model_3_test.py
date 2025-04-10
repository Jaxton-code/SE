import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error

# Load model
model = joblib.load('bike_forecast_xgb.pkl')

# Load merged dataset
merged_df = pd.read_csv("merged_bike_weather_data.csv")
merged_df['timestamp'] = pd.to_datetime(merged_df['timestamp'], format='mixed', errors='coerce')
merged_df.dropna(subset=['timestamp'], inplace=True)

# Feature engineering (match ml_model3.py)
merged_df['hour'] = merged_df['timestamp'].dt.hour
merged_df['day_of_week'] = merged_df['timestamp'].dt.dayofweek
merged_df['is_weekend'] = merged_df['day_of_week'].isin([5, 6]).astype(int)
merged_df['month'] = merged_df['timestamp'].dt.month

# Ensure 'number' is present if model used it
if 'number' not in merged_df.columns:
    station_info = pd.read_csv("/Users/shaneobrien/desktop/SE/station_info.csv")
    merged_df = pd.merge(merged_df, station_info[['address', 'number']], on='address', how='left')

# Drop rows with missing values
merged_df.dropna(inplace=True)

# Match expected feature order
expected_features = model.feature_names_in_
X = merged_df[expected_features]
y = merged_df['available_bikes']

# Time-based split (as done in ml_model3.py)
split_idx = int(len(X) * 0.8)
X_test = X.iloc[split_idx:]
y_test = y.iloc[split_idx:]

# Predict
preds = model.predict(X_test)

# Plot predictions vs actual
plt.figure(figsize=(12, 6))
plt.plot(y_test.values[:100], label='Actual', marker='o')
plt.plot(preds[:100], label='Predicted', marker='x')
plt.title("ML Model 3 - Predicted vs Actual Bikes (First 100 samples)")
plt.xlabel("Sample Index")
plt.ylabel("Available Bikes")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("ml_model3_pred_vs_actual.png")
plt.show()

# Print MAE
mae = mean_absolute_error(y_test, preds)
print(f"Model 3 MAE: {mae:.2f}")
