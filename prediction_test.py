import joblib
import json
import pandas as pd
from datetime import datetime

# Step 1: Load cluster map
with open("models_per_cluster/station_cluster_map.json") as f:
    cluster_map = json.load(f)



now = datetime.now()
hour = now.hour
day_of_week = now.weekday()
month = now.month


# Step 2: Input from user
station_number = 83
features_input = {
    "hour": hour,
    "day_of_week": day_of_week,
    "is_weekend": 0,
    "month": month,
    "temperature": 12.0,
    "wind": 4.2,
    "number": station_number
}

# Step 3: Find cluster and load model
cluster_id = cluster_map[str(station_number)]
model_bundle = joblib.load(f"models_per_cluster/cluster_{cluster_id}.pkl")
model = model_bundle['model']
features = model_bundle['features']

# Step 4: Prepare data and predict
X = pd.DataFrame([features_input])[features]
prediction = model.predict(X)[0]

print(f"📍 Predicted bikes available at station {station_number}: {prediction:.2f}")
