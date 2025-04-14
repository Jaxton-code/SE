def save_snapshot(station_data):
    import sqlite3
    import datetime

    conn = sqlite3.connect('bikes.db')
    c = conn.cursor()

    for station in station_data:
        c.execute("""
            INSERT INTO bike_station_data 
            (station_name, available_bikes, available_stands, status, lat, lng, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            station['name'],
            station['available_bikes'],
            station['available_bike_stands'],
            station['status'],
            station['position']['lat'],
            station['position']['lng'],
            datetime.datetime.now()
        ))

    conn.commit()
    conn.close()
#testing
def get_station_data():
        return [{"name": "Station A", "available_bikes": 4, "available_bike_stands": 6, "status": "OPEN", "position": {"lat": 53.34, "lng": -6.26}}]

def save_all_stations():
    data = get_station_data()
    if not data:
        raise ValueError("No data fetched.")
    save_snapshot(data)
