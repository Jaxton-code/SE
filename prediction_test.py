import joblib
import pandas as pd

# Load the saved model
model = joblib.load('bike_prediction_model.pkl')

# Prepare new data (must have the same features used during training)
# Based on your code, these features are: 'hour', 'day_of_week', 'is_weekend', 'temperature', 'wind', 'number'
new_data = pd.DataFrame({
    'hour': [12, 13, 14],
    'day_of_week': [0, 1, 2],
    'is_weekend': [0, 0, 0],
    'temperature': [22.5, 23.1, 24.0],
    'wind': [5.2, 6.1, 4.8],
    'number': [1, 42, 42]  # Station number or similar identifier
})

# Make predictions
predictions = model.predict(new_data)
print("Predicted available bikes:", predictions)