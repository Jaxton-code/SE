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

    c.execute("DELETE FROM bike_station_data WHERE timestamp < datetime('now', '-24 hours')")
    conn.commit()
    conn.close()
