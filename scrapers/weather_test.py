import requests
JCKEY_WEATHER = 'd303018b3ae7074cc779843fcac927dd'
WEATHER_URI = f"https://api.openweathermap.org/data/2.5/weather?q=Dublin,IE&appid={JCKEY_WEATHER}"
response = requests.get(WEATHER_URI)
print(response.status_code)
print(response.text)
