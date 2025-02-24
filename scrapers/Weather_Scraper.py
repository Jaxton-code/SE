import sqlalchemy as sqla
from sqlalchemy import create_engine, text
import traceback
import simplejson as json
import requests
import datetime
from pprint import pprint
#mport dbinfo
import os
import csv


JCKEY = 'd303018b3ae7074cc779843fcac927dd'
NAME = "dublin"
STATIONS_URI = f"https://api.openweathermap.org/data/2.5/weather?q=Dublin,IE&appid={JCKEY}"

FORE_CAST = "https://api.openweathermap.org/data/2.5/forecast?q=Dublin,IE&appid=YOUR_API_KEY"

response_weather = requests.get(STATIONS_URI).text
weather_Json = json.loads(response_weather)
json_str = json.dumps(weather_Json, indent=3)
print(json_str)

#####Function to import the Weather Data##### 

def weather_to_db (api_text, engine):
    weather_data = json.loads(api_text)
    print("Weather data received", type(weather_data))

    # need to conver fahernheit temperature to celcius 

    current_temp = weather_data['main']['temp']
    feels_like_current = weather_data['main']['feels_like']
    conversion_current = (current_temp - 272.15) #convert to celcius
    conversion_feels_like = (feels_like_current- 272.15)



    with engine.begin () as conn: 
        try:
            vals = { 
                "city_id": weather_data['id'], #city id
                "coord_lon": str(weather_data['coord']['lon']),
                "coord_lat": str(weather_data['coord']['lat']),
                "weather_id": weather_data['weather'][0]['id'],
                'weather_main':weather_data['weather'][0]['main'],
                "temp": conversion_current,
                "temp_feel":conversion_feels_like,
                "wind_speed":weather_data['wind']['speed'],
                "clouds":weather_data['clouds']['all'],
                "sunrise": datetime.datetime.fromtimestamp(weather_data['sys']['sunrise']),
                "sunset": datetime.datetime.fromtimestamp(weather_data['sys']['sunset']),
      
            }
            sql = text( """
                        INSERT INTO weather_info (city_id, coord_lon, coord_lat, weather_id, weather_main,temp, temp_feel, wind_speed, clouds, sunrise, sunset)
                        VALUES (:city_id, :coord_lon,:coord_lat, :weather_id, :weather_main, :temp,:temp_feel, :wind_speed, :clouds, :sunrise, :sunset)
                       
                        """
                      )
                    
            conn.execute(sql,vals)
        except Exception as e:
            print("Error processing weather data:" , weather_data)
            print(traceback.format_exc())


####### Function to backup weather to .csv  ######


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



############# Create the weather  table ############
sql_weather = text('''
CREATE TABLE IF NOT EXISTS weather_info (
    unique_id INT AUTO_INCREMENT PRIMARY KEY, 
    weather_id INT NOT NULL ,
    city_id INT NOT NULL, 
    coord_lon VARCHAR(20) NOT NULL,
    coord_lat VARCHAR(20) NOT NULL,
    weather_main VARCHAR(20) NOT NULL,
    temp FLOAT NOT NULL,
    temp_feel FLOAT NOT NULL,
    wind_speed FLOAT NOT NULL,
    clouds INT NULL,
    sunrise DATETIME NULL,
    sunset DATETIME NULL,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP  COMMENT 'set the create time'
);
''')

with engine.begin() as conn:
    conn.execute(sql_weather)
    

with engine.connect() as conn:
    tab_structure = conn.execute(text("SHOW COLUMNS FROM  weather_info;"))
    columns = tab_structure.fetchall()
    print("Weather table structure:")
    pprint(columns)



            
############## Run the API request for station data ##############


    try:
        r = requests.get(STATIONS_URI)
        if r.status_code == 200:
            weather_to_db(r.text, engine)
            with engine.connect() as conn:
                res = conn.execute(text("SELECT * FROM weather_info"))
                rows = res.fetchall()
                print("Weather table data:")
                print(rows)
        else:
            print("Error fetching station data, status code:", r.status_code)
    except Exception as e:
        print(traceback.format_exc())
        


    #### write table to csv ###
    backup_table_to_csv(engine, "weather_info", "weather_data")
  

















