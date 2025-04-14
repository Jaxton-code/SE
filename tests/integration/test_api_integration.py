import unittest
from unittest.mock import patch
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app import app

class TestAPIIntegration(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @patch('app.requests.get')
    def test_station_api_integration(self, mock_get):
        # Mock JCDecaux API JSON response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{
            "number": 1,
            "name": "Test Station",
            "address": "Test Address",
            "position": {"lat": 53.34, "lng": -6.26},
            "available_bikes": 5,
            "available_bike_stands": 10,
            "status": "OPEN"
        }]
        response = self.client.get('/api/stations')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data[0]['name'], "Test Station")
        self.assertIn("available_bike_stands", json_data[0])

    @patch('app.requests.get')
    def test_weather_api_integration(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "main": {"temp": 283.15, "feels_like": 280.0},
            "weather": [{"main": "Cloudy"}],
            "wind": {"speed": 5.0},
            "clouds": {"all": 85},
            "sys": {"sunrise": 1700000000, "sunset": 1700040000}
        }

        response = self.client.get('/api/weather')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertIn("temp", json_data)
        self.assertEqual(json_data["weather_main"], "Cloudy")

if __name__ == '__main__':
    unittest.main()

