import joblib
import numpy as np
import pandas as pd

# Load model for station’s cluster
model_data = joblib.load('models_per_cluster/cluster_0.pkl')  # Replace X with actual cluster ID for Portobello
model, features = model_data['model'], model_data['features']

# Check your input features carefully
input_features = {
    'hour': 15,
    'day_of_week': 4,  # Friday
    'is_weekend': 0,
    'month': 4,
    'temperature': actual_temperature,  # current actual temp
    'wind': actual_wind_speed,          # current actual wind
    'is_peak_morning': 0,
    'is_peak_evening': 0,
    'weather_code': actual_weather_code,  
    'station_bike_capacity': 30,
    'station_mean_bikes': historical_mean,
    'station_std_bikes': historical_std,
    'avg_bikes_hour_dow': avg_historical_usage,
    'time_cluster': time_cluster,
    'number': station_number
}

# Predict
input_vector = np.array([input_features[f] for f in features]).reshape(1, -1)
predicted_bikes = model.predict(input_vector)[0]
print(predicted_bikes)
