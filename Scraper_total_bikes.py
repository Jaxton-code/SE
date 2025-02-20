import sqlalchemy as sqla
from sqlalchemy import create_engine, text
import traceback
import simplejson as json
import requests
import datetime
from pprint import pprint
import dbinfo
import os
import csv
import pymysql



response_bikes = requests.get(dbinfo.STATIONS_URI).text
response_bikes_Json = json.loads(response_bikes)
json_str = json.dumps(response_bikes_Json, indent=3)
print(json_str)

############## Function to import station data from JCDecaux API ##########
def stations_to_db(api_text, engine):
    stations = json.loads(api_text)
   
    
    with engine.begin() as conn:
        for station in stations:
            try:
                position = station.get("position", {})  # Ensure 'position' exists
                position_lat = position.get("lat", None)  # Extract latitude
                position_lng = position.get("lng", None)  # Extract longitude
                
                vals = {
                    "number": int(station.get('number')),
                    "address": station.get('address'),
                    "banking": int(station.get('banking')),
                    "bikestands": int(station.get('bike_stands')),
                    "name": station.get('name'),
                    "status": station.get('status'),
                    "position_lat": position_lat,
                    "position_lng": position_lng,
                }
                sql = text("""
                    INSERT INTO station (number,address, banking, bikestands, name, status, position_lat, position_lng)
                    VALUES (:number, :address, :banking, :bikestands, :name, :status, :position_lat, :position_lng)
                    ON DUPLICATE KEY UPDATE;
                        address = VALUES(address),
                        banking = VALUES(banking),
                        bikestands = VALUES(bikestands),
                        status = VALUES(status),
                        position_lat = VALUES(position_lat),
                        position_lng = VALUES(position_lng)
                    
                """)
                conn.execute(sql, vals)
            except Exception as e:
                print("Error processing station:", station)
                print(traceback.format_exc())

############## Function to import/update availability data ##########
def availability_to_db(api_text, engine):
    availabilities = json.loads(api_text)
    print("Availability data type:", type(availabilities), "Number of entries:", len(availabilities))
    
    with engine.begin() as conn:
        for station in availabilities:
            try:
                # Convert the epoch timestamp (in ms) to a datetime string
                ts = station.get('last_update')
                dt_str = datetime.datetime.fromtimestamp(int(ts) / 1000).strftime("%Y-%m-%d %H:%M:%S")
                
                vals = {
                    "number": int(station.get('number')),
                    "available_bikes": int(station.get('available_bikes')),
                    "available_bike_stands": int(station.get('available_bike_stands')),
                    "status": station.get('status'),
                    "last_update": dt_str
                }
                sql = text("""
                    INSERT INTO availability (number, available_bikes, available_bike_stands, status, last_update)
                    VALUES (:number, :available_bikes, :available_bike_stands, :status, :last_update)
        
                """)
                conn.execute(sql, vals)
            except Exception as e:
                print("Error processing availability for station:", station)
                print(traceback.format_exc())



### write old table to CSV FILE ######


def backup_table_to_csv(engine, table_name, output_folder):
    # Query the table data
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT * FROM {table_name}"))
        rows = result.fetchall()
        keys = result.keys()
    
    os.makedirs(output_folder, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{table_name}_backup_{timestamp}.csv"
    filepath = os.path.join(output_folder, filename)
    
    with open(filepath, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(keys)  # header row
        writer.writerows(rows)
    
    print(f"Backup of '{table_name}' saved to {filepath}")


###################### Connect to the DB ######################
USER = "root"
PASSWORD = "appele12"
PORT = "3306"
DB = "local_databasejcdecaux"
URI = "127.0.0.1"

connection_string = "mysql+pymysql://{}:{}@{}:{}/{}".format(USER, PASSWORD, URI, PORT, DB)
engine = create_engine(connection_string, echo=True)

# Create the database (if needed)
with engine.begin() as conn:
    conn.execute(text("CREATE DATABASE IF NOT EXISTS local_databasejcdecaux;"))
    conn.commit()

############# Create the station table ############
sql_station = text('''
CREATE TABLE IF NOT EXISTS station (
    number INTEGER PRIMARY KEY,              
    name VARCHAR(256) ,
    address VARCHAR(256), 
    banking INTEGER,
    bikestands INTEGER,
    status VARCHAR(256),
    position_lat DOUBLE,
    position_lng DOUBLE
);
''')
with engine.begin() as conn:
    conn.execute(sql_station)
    conn.commit()

with engine.connect() as conn:
    tab_structure = conn.execute(text("SHOW COLUMNS FROM station;"))
    columns = tab_structure.fetchall()
    print("Station table structure:")
    print(columns)

############# Create the availability table ############
sql_availability = text('''
CREATE TABLE IF NOT EXISTS availability (
    id INT AUTO_INCREMENT PRIMARY KEY,                    
    number INTEGER ,
    available_bikes INTEGER,
    available_bike_stands INTEGER,
    status VARCHAR(256),
    last_update DATETIME,
    FOREIGN KEY (number) REFERENCES station(number) ON DELETE CASCADE                    
);
''')
with engine.begin() as conn:
    conn.execute(sql_availability)
    conn.commit()

with engine.connect() as conn:
    tab_structure = conn.execute(text("SHOW COLUMNS FROM availability;"))
    columns = tab_structure.fetchall()
    print("Availability table structure:")
    pprint(columns)

############## Run the API request for station data ##############
try:
    r = requests.get(dbinfo.STATIONS_URI, params={"apiKey": dbinfo.JCKEY, "contract": dbinfo.NAME})
    if r.status_code == 200:
        stations_to_db(r.text, engine)
        with engine.connect() as conn:
            res = conn.execute(text("SELECT * FROM station"))
            rows = res.fetchall()
            print("Station table data:")
            pprint(rows)
    else:
        print("Error fetching station data, status code:", r.status_code)
except Exception as e:
    print(traceback.format_exc())

############## Run the API request for availability data ##############
try:
    # Assuming the same endpoint returns both station and availability data.
    r_avail = requests.get(dbinfo.STATIONS_URI, params={"apiKey": dbinfo.JCKEY, "contract": dbinfo.NAME})
    if r_avail.status_code == 200:
        availability_to_db(r_avail.text, engine)
        with engine.connect() as conn:
            res = conn.execute(text("SELECT * FROM availability"))
            rows = res.fetchall()
            print("Availability table data:")
            pprint(rows)
    else:
        print("Error fetching availability data, status code:", r_avail.status_code)
except Exception as e:
    print(traceback.format_exc())


#### write table to csv ###
backup_table_to_csv(engine, "availability", "bike_data")