import unittest
import joblib
import os
import numpy as np

class TestMLPredictions(unittest.TestCase):
    def setUp(self):
        # Adjust path if needed
        self.model_dir = "models_per_cluster"
        self.example_input = {
            'hour': 14,
            'day_of_week': 2,
            'is_weekend': 0,
            'month': 4,
            'temperature': 13.0,
            'wind': 3.5,
            'number': 42  # station number
        }

    def test_model_files_exist(self):
        models = [f for f in os.listdir(self.model_dir) if f.endswith('.pkl')]
        self.assertGreater(len(models), 0, "No model files found.")

    def test_model_prediction_runs(self):
        model_file = os.path.join(self.model_dir, "cluster_0.pkl")
        if os.path.exists(model_file):
            bundle = joblib.load(model_file)
            model = bundle['model']
            features = bundle['features']
            X = np.array([[self.example_input.get(f, 0) for f in features]])
            prediction = model.predict(X)
            self.assertTrue(prediction[0] >= 0, "Prediction should be non-negative.")
        else:
            self.skipTest("cluster_0.pkl not found for testing")

if __name__ == '__main__':
    unittest.main()
