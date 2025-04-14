# tests/test_save_stations.py

import unittest
from unittest.mock import patch
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import save_stations_for_db

class TestSaveStations(unittest.TestCase):

    @patch('save_stations_for_db.get_station_data')
    @patch('save_stations_for_db.save_snapshot')
    def test_save_stations_success(self, mock_save, mock_fetch):
        mock_data = [{'name': 'Test Station', 'available_bikes': 4, 'available_bike_stands': 6,
                      'status': 'OPEN', 'position': {'lat': 53.3, 'lng': -6.2}}]
        mock_fetch.return_value = mock_data
        save_stations_for_db.save_all_stations()
        mock_save.assert_called_once_with(mock_data)

    @patch('save_stations_for_db.get_station_data')
    def test_save_stations_no_data(self, mock_fetch):
        mock_fetch.return_value = []
        with self.assertRaises(ValueError):
            save_stations_for_db.save_all_stations()

    @patch('save_stations_for_db.get_station_data')
    def test_save_stations_api_failure(self, mock_fetch):
        mock_fetch.side_effect = Exception("API Error")
        with self.assertRaises(Exception) as context:
            save_stations_for_db.save_all_stations()
        self.assertIn("API Error", str(context.exception))
