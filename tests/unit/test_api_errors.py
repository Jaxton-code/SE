import unittest
from unittest.mock import patch
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

def setUp(self):
    self.client = app.test_client()

@patch('app.requests.get')
def test_jcdecaux_timeout(self, mock_get):
    mock_get.side_effect = TimeoutError("Timeout occurred")
    response = self.client.get('/api/stations')
    self.assertEqual(response.status_code, 500)
    self.assertIn("Timeout", response.get_data(as_text=True))

@patch('app.requests.get')
def test_jcdecaux_connection_error(self, mock_get):
    mock_get.side_effect = ConnectionError("Connection failed")
    response = self.client.get('/api/weather')
    self.assertEqual(response.status_code, 500)
    self.assertIn("Connection failed", response.get_data(as_text=True))

@patch('app.requests.get')
def test_jcdecaux_http_error(self, mock_get):
    mock_get.return_value.status_code = 404
    mock_get.return_value.json.return_value = {"error": "Not found"}
    response = self.client.get('/api/stations')
    self.assertEqual(response.status_code, 200)  # Fallback if no exception
    # Depending on the logic in your code, might need to simulate raise_for_status()
