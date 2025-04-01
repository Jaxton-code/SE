import requests
import json
import csv

# API Config
API_KEY = "8b54a4b00f518f57734cf66e4009bda64f52c4ac"
CONTRACT_NAME = "dublin"
STATIONS_URI = "https://api.jcdecaux.com/vls/v1/stations"

# Output file
output_file = "station_info.csv"

def fetch_and_save_station_info():
    try:
        # Send API request
        response = requests.get(STATIONS_URI, params={"apiKey": API_KEY, "contract": CONTRACT_NAME})
        response.raise_for_status()
        stations = response.json()

        # Extract and save to CSV
        with open(output_file, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["number", "latitude", "longitude", "name"])  # header

            for station in stations:
                station_number = station.get("number")
                lat = station.get("position", {}).get("lat")
                lng = station.get("position", {}).get("lng")
                name = station.get("name")

                if station_number is not None and lat is not None and lng is not None:
                    writer.writerow([station_number, lat, lng, name])

        print(f"✅ Saved {len(stations)} stations to '{output_file}'")

    except Exception as e:
        print(" Failed to fetch station data:", e)

if __name__ == "__main__":
    fetch_and_save_station_info()
