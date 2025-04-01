from flask import Flask,render_template, jsonify, request
import joblib
import numpy as np
import pandas as pd
import requests
import datetime
import random
import csv
from datetime import datetime, timedelta

app = Flask(__name__,static_folder='static', template_folder='templates')
model = joblib.load("/Users/shaneobrien/Desktop/SE/models_per_cluster/cluster_0.pkl")

# API URLs
JCKEY_STATION = '8b54a4b00f518f57734cf66e4009bda64f52c4ac'
JCKEY_WEATHER = 'd303018b3ae7074cc779843fcac927dd'
STATIONS_URI = f"https://api.jcdecaux.com/vls/v1/stations?contract=Dublin&apiKey={JCKEY_STATION}"
WEATHER_URI = f"https://api.openweathermap.org/data/2.5/weather?q=Dublin,IE&appid={JCKEY_WEATHER}"


#mapping station number to station name
# def load_station_lookup(path='station_info.csv'):
#     lookup = {}
#     try:
#         with open(path, newline='') as csvfile:
#             reader = csv.DictReader(csvfile)
#             for row in reader:
#                 name = row['name'].strip().upper()
#                 number = int(row['number'])
#                 lookup[name] = number
#     except Exception as e:
#         print("Failed to load station lookup:", e)
#     return lookup

#load the station
#station_lookup = load_station_lookup()


@app.route('/api/stations', methods=['GET'])
def get_live_stations():
    try:
        response = requests.get(STATIONS_URI)
        station_data = response.json()
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
                "temp": round(weather_data['main']['temp'] - 273.15, 2),  # Convert from Kelvin to Celsius
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
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500
       

@app.route('/')
def home():
    return  render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/predict', methods=['POST'])
def predict ():
    try:
        data = request.get_json()
        features = np.array([[
            data['hour'],
            data['day_of_week'],
            data['is_weekend'],
            data['temperature'],
            data['wind'],
            data['number']
        ]])

        prediction = model.predict(features[0])
        return jsonify({'prediction': round(prediction)})
    except Exception as e:
        return jsonify({'error': str(e)})
    

@app.route('/api/trend/<station_name>', methods=['GET'])
def get_station_trend(station_name):
    labels = []
    values = []
    now = datetime.now()
    ow = datetime.now()
    labels = []
    values = []

    # Randomize a  value per station so each has its own originality
    base_value = random.randint(3, 15)
    
    for i in range(24):
        hour_time = now - timedelta(hours=23 - i)  # oldest first
        labels.append(hour_time.strftime('%H:%M'))
        hour = hour_time.hour
        # Simulate some realistic fluctuation
        value = max(0, base_value + random.randint(-4, 4))

        if 6 <= hour <= 9:  # Morning rush
         value += 3

        elif 17 <= hour <= 19:  # Evening rush
            value += 2
        elif 0 <= hour <= 5:  # Late night
            value -= 2
        elif 10 <= hour <= 15:  # Midday 
            value -= 1

        # Keep value non-negative
        values.append(max(0, value))
        
        values.append(value)

    return jsonify({
        "labels": labels,
        "values": values
    })


if __name__ == '__main__':
    app.run(host = '0.0.0.0', port=5000)
