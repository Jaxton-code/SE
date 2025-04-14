from flask import Flask, render_template, jsonify, request
import joblib
import numpy as np
import pandas as pd
import requests
import datetime
import random
import csv
import os
from datetime import datetime, timedelta
from save_stations_for_db import save_snapshot
import sqlite3
import json
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bikes.db')


app = Flask(__name__, static_folder='static', template_folder='templates')

# API Keys
JCKEY_STATION = '8b54a4b00f518f57734cf66e4009bda64f52c4ac'
JCKEY_WEATHER = 'd303018b3ae7074cc779843fcac927dd'

# API URLs
STATIONS_URI = f"https://api.jcdecaux.com/vls/v1/stations?contract=Dublin&apiKey={JCKEY_STATION}"
WEATHER_URI = f"https://api.openweathermap.org/data/2.5/weather?q=Dublin,IE&appid={JCKEY_WEATHER}"


with open('models_per_cluster/time_usage_cluster_map.json', 'r') as f:
    station_to_cluster = json.load(f)
    station_to_cluster = {int(k): v for k, v in station_to_cluster.items()}

with open("station_metadata.json", "r") as f:
    station_metadata = json.load(f)


# Define the exact order of features expected by  model
expected_feature_order = [
    'hour',
    'day_of_week',
    'is_weekend',
    'month',
    'temperature',
    'wind_speed',
    'is_peak_morning',
    'is_peak_evening',
    'weather_code',
    'station_bike_capacity',
    'station_mean_bikes',
    'station_std_bikes',
    'avg_bikes_hour_dow',
    'time_cluster',
    'number'
]



def extract_time_from_user(user_datetime):
    dt = datetime.strptime(user_datetime, "%Y-%m-%d %H:%M")
    hour = dt.hour
    return {
        "hour": hour,
        "day_of_week": dt.weekday(),
        "is_weekend":int(dt.weekday() >= 5),
        "month": dt.month,
        "is_peak_morning": int(7 <= hour <= 10),
        "is_peak_evening": int(16 <= hour <= 19)
    }


@app.route('/api/stations/debug')
def debug_stations():
    try:
        response = requests.get(STATIONS_URI)
        print("Raw response:", response.text[:500])  # print just first 500 chars
        return response.text
    except Exception as e:
        return str(e), 500


def get_weather_forecast(user_datetime):
    target_ts = int(user_datetime.timestamp())
    response = requests.get(
        f"https://api.openweathermap.org/data/2.5/forecast?q=Dublin,IE&appid={JCKEY_WEATHER}"
    )
    data = response.json()
    closest = min(data['list'], key=lambda x: abs(x['dt'] - target_ts))

    weather_main = closest['weather'][0]['main']
    weather_condition_map = {
        "Clear": 0,
        "Clouds": 1,
        "Mist": 2,
        "Drizzle": 3,
        "Rain": 4,
        "Snow": 5,
        "Thunderstorm": 6,
        "Fog": 2
    }

    return {
        "temperature": round(closest['main']['temp'] - 273.15, 2),
        "clouds": closest['clouds']['all'],
        "wind_speed": closest['wind']['speed'],
        "weather_main": weather_main,
        "weather_code": weather_condition_map.get(weather_main, -1)  
        
    }

def build_feature(user_datetime):
    dt = datetime.strptime(user_datetime, "%Y-%m-%d %H:%M")

    time_feats = extract_time_from_user(user_datetime)
    weather_feats = get_weather_forecast(dt)

    return {**time_feats, **weather_feats}



@app.route('/api/stations', methods=['GET'])
def get_live_stations():
    try:
        response = requests.get(STATIONS_URI)
        station_data = response.json()
        


        if not isinstance(station_data, list):
            print("Unexpected response from JCDecaux:", station_data)
            return jsonify({"error": "JCDecaux API returned unexpected data"}), 500
       
       
        save_snapshot(station_data) 
        formatted_data = [
            {
                "number": station['number'],
                "address": station['address'],
                "name": station['name'],
                "position_lat": station['position']['lat'],
                "position_lng": station['position']['lng'],
                "available_bikes": station['available_bikes'],
                "available_bike_stands": station['available_bike_stands'],
                "status": station['status']
            }
            for station in station_data
        ]
        return jsonify(formatted_data)
    except Exception as e:
        print("Error in /api/stations:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/weather', methods=['GET'])
def get_live_weather():
    try:
        response = requests.get(WEATHER_URI)
        if response.status_code == 200:
            weather_data = response.json()
            formatted_weather = {
                "temp": round(weather_data['main']['temp'] - 273.15, 2),
                "temp_feel": round(weather_data['main']['feels_like'] - 273.15, 2),
                "weather_main": weather_data['weather'][0]['main'],
                "wind_speed": weather_data['wind']['speed'],
                "clouds": weather_data['clouds']['all'],
                "sunrise": datetime.fromtimestamp(weather_data['sys']['sunrise']).strftime('%H:%M:%S'),
                "sunset": datetime.fromtimestamp(weather_data['sys']['sunset']).strftime('%H:%M:%S')
            }
            return jsonify(formatted_weather)
        else:
            return jsonify({"error": f"Failed to fetch weather data: {response.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/predict', methods=['POST'])
@app.route('/predict', methods=['GET'])
def predict():
    try:
        station_number = request.args.get('station_number')
        datetime_str = request.args.get('datetime')

        print("Received /predict request:", station_number, datetime_str)

        if not station_number or not datetime_str:
            return jsonify({'error': 'Missing station_number or datetime'}), 400

        station_number = int(station_number)
        cluster = station_to_cluster.get(station_number)
        print("Cluster lookup result:", cluster)

        if cluster is None:
            return jsonify({'error': f'Station number {station_number} not in cluster map'}), 400

        # STEP 1: Extract dynamic (time/weather) features
        features = build_feature(datetime_str)

        # STEP 2: Inject station-specific metadata (merged in here!)
        features.update(station_metadata.get(str(station_number), {}))

        defaults = {
        'station_bike_capacity': 30,
        'station_mean_bikes': 10,
        'station_std_bikes': 5,
        'avg_bikes_hour_dow': 10,  #  
}
        for k, v in defaults.items():
            features.setdefault(k, v)

        # STEP 3: Final input vector
        features['number'] = station_number
        input_vector = np.array([[features[key] for key in expected_feature_order]])

        # STEP 4: Load model & predict
        model_path = f'models_per_cluster/cluster_{cluster}.pkl'
        model_bundle = joblib.load(model_path)
        model = model_bundle['model']  # Extract the actual model
        prediction = model.predict(input_vector)[0]

        prediction = model.predict(input_vector)[0]

        return jsonify({
            'station_number': station_number,
            'datetime': datetime_str,
            'prediction': round(prediction),
            'features': features
        })

    except Exception as e:
        print("Exception occurred in /predict route:", str(e))
        return jsonify({'error': str(e)}), 500




@app.route('/api/trend/<station_name>', methods=['GET'])
def get_station_trend(station_name):
    try:
        conn = sqlite3.connect(DB_PATH)
        query = """
                
            SELECT timestamp, available_bikes
            FROM bike_station_data
            WHERE station_name = ?
              AND timestamp >= datetime('now', '-24 hours')
            ORDER BY timestamp;
        """
        df = pd.read_sql_query(query, conn, params=(station_name,))
        conn.close()

        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        return df.to_json(orient='records')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


    # # Simulated data for testing
    # labels = []
    # values = []
    # now = datetime.now()

    # base_value = random.randint(3, 15)

    # for i in range(24):
    #     hour_time = now - timedelta(hours=23 - i)
    #     labels.append(hour_time.strftime('%H:%M'))
    #     hour = hour_time.hour

    #     value = max(0, base_value + random.randint(-4, 4))

    #     if 6 <= hour <= 9:
    #         value += 3
    #     elif 17 <= hour <= 19:
    #         value += 2
    #     elif 0 <= hour <= 5:
    #         value -= 2
    #     elif 10 <= hour <= 15:
    #         value -= 1

    #     values.append(max(0, value))

    # return jsonify({
    #     "labels": labels,
    #     "values": values
    # })

import threading
import time

def auto_snapshot():
    while True:
        try:
            print("[AutoSnapshot] Saving live station data...")
            response = requests.get(STATIONS_URI)
            station_data = response.json()
            save_snapshot(station_data)
        except Exception as e:
            print("[AutoSnapshot] Error saving snapshot:", e)
        time.sleep(60)  # every 60 seconds

if __name__ == '__main__':
    threading.Thread(target=auto_snapshot, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)