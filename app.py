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

app = Flask(__name__, static_folder='static', template_folder='templates')

# API Keys
JCKEY_STATION = '8b54a4b00f518f57734cf66e4009bda64f52c4ac'
JCKEY_WEATHER = 'd303018b3ae7074cc779843fcac927dd'

# API URLs
STATIONS_URI = f"https://api.jcdecaux.com/vls/v1/stations?contract=Dublin&apiKey={JCKEY_STATION}"
WEATHER_URI = f"https://api.openweathermap.org/data/2.5/weather?q=Dublin,IE&appid={JCKEY_WEATHER}"


with open('station_cluster_map.json', 'r') as f:
    station_to_cluster = json.load(f)

def extract_time_from_user(user_datetime):
    dt = datetime.strptime(user_datetime,"Y%-m%-%d %H:%M")
    return {
        "hour": dt.hour,
        "day_of_week": dt.weekday(),
        "is_weekend":int(dt.weekday() >= 5)
    }



def get_weather_forecast(user_datetime):
    target_ts = int(user_datetime.timestamp())
    response = requests.get(
        f"https://api.openweathermap.org/data/2.5/forecast?q=Dublin,IE&appid={JCKEY_WEATHER}"
    )
    data = response.json()

    closest = min(data['list'], key=lambda x: abs(x['dt'] - target_ts))

    return {
        "forecast_temp": round(closest['main']['temp'] - 273.15, 2),
        "clouds": closest['clouds']['all'],
        "wind_speed": closest['wind']['speed'],
        "weather_main": closest['weather'][0]['main']
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

        save_snapshot(station_data) 
        formatted_data = [
            {
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
        datetime_str = request.args.get('datetime')  # Format: "2025-04-05 14:30"

        if not station_number or not datetime_str:
            return jsonify({'error': 'Missing station_number or datetime'}), 400

        try:
            station_number = int(station_number)
        except ValueError:
            return jsonify({'error': 'station_number must be an integer'}), 400

        # Lookup cluster
        cluster = station_to_cluster.get(station_number)
        if cluster is None:
            return jsonify({'error': f'Station number {station_number} not in cluster map'}), 400

        # Build feature vector
        features = build_feature(datetime_str)

        # Include the station number if your model expects it
        features['number'] = station_number

        input_vector = np.array([[
            features['hour'],
            features['day_of_week'],
            features['is_weekend'],
            features['forecast_temp'],
            features['wind_speed'],
            features['number']
        ]])

        # Load model for this cluster
        model_path = os.path.join('models_per_cluster', f'cluster_{cluster}.pkl')
        model = joblib.load(model_path)

        prediction = model.predict(input_vector)[0]

        return jsonify({
            'station_number': station_number,
            'datetime': datetime_str,
            'prediction': round(prediction),
            'features': features
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/trend/<station_name>', methods=['GET'])
def get_station_trend(station_name):


    conn = sqlite3.connect('bikes.db')

    query ="""" " \
    SELECT timestamp, available_bikes
    FROM bike_station_data
    WHERE station_nae = ?
     AND timestamp >= datetime('now, '-24 hours')
    ORDER BY timestamp
    """

    df = pd.read_sql_query(query, conn, params=(station_name,))
    conn.close()

    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')

    return df.to_json(orient='records')
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)