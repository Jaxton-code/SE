from flask import Flask,render_template, jsonify
import requests
import datetime

app = Flask(__name__,static_folder='static', template_folder='templates')

# API URLs
JCKEY_STATION = '8b54a4b00f518f57734cf66e4009bda64f52c4ac'
JCKEY_WEATHER = 'd303018b3ae7074cc779843fcac927dd'
STATIONS_URI = f"https://api.jcdecaux.com/vls/v1/stations?contract=Dublin&apiKey={JCKEY_STATION}"
WEATHER_URI = f"https://api.openweathermap.org/data/2.5/weather?q=Dublin,IE&appid={JCKEY_WEATHER}"

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
                "sunrise": datetime.datetime.fromtimestamp(weather_data['sys']['sunrise']).strftime('%H:%M:%S'),
                "sunset": datetime.datetime.fromtimestamp(weather_data['sys']['sunset']).strftime('%H:%M:%S')
            }
            return jsonify(formatted_weather)
        else:
            return jsonify({"error": f"Failed to fetch weather data: {response.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return  render_template('index.html')

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port=5000)
