import sqlite3

conn = sqlite3.connect('bikes.db')
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS bike_station_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_name TEXT,
    available_bikes INTEGER,
    available_stands INTEGER,
    status TEXT,
    lat REAL,
    lng REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()
