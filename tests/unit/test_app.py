import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app


class FlaskAPITestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_stations_endpoint(self):
        response = self.app.get('/api/stations')
        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.get_json()[0])

    def test_weather_endpoint(self):
        response = self.app.get('/api/weather')
        self.assertEqual(response.status_code, 200)
        self.assertIn("temp", response.get_json())

if __name__ == '__main__':
    unittest.main()
