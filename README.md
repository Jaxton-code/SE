# Dublin Bikes Sharing System

## 📌 Project Description
This project is a web-based bike sharing system that provides real-time DublinBikes data visualization, combined with weather information and a machine learning model to predict station occupancy.

## 🚀 Main Features
- **Bike station data scraping**: Retrieve real-time station information from the JCDecaux API (every 5 minutes).
- **Weather data scraping**: Retrieve weather data from the OpenWeather API (every hour).
- **Data storage**: Use AWS RDS (MySQL) for database management.
- **Data visualization**: Display station occupancy on Google Maps.
- **Data interaction**: Show historical occupancy trends (hourly/daily) when a station is clicked.
- **Machine learning prediction**: Predict future station occupancy based on historical data.

## 🛠️ Tech Stack
- **Backend**: Python (Flask)
- **Frontend**: HTML / JavaScript / CSS
- **Database**: MySQL (AWS RDS)
- **Server**: AWS EC2
- **Data Visualization**: Google Maps API
- **Machine Learning**: Pandas, Scikit-learn

## 💾 Environment and Dependencies
### 1️⃣ Install Python dependencies
```bash
pip install -r requirements.txt
```
### 2️⃣ Set environment variables
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
```

## 📌 Setup and Run
### 1️⃣ Clone the repository
```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/DublinBikesProject.git
cd DublinBikesProject
```
### 2️⃣ Run the backend API
```bash
python app.py
```
### 3️⃣ Access the frontend
Open your browser and go to `http://localhost:5000`

## 🔗 API Documentation
### Get all station data
```http
GET /api/stations
```
Response:
```json
[
  {
    "id": 42,
    "name": "STATION NAME",
    "available_bikes": 5,
    "available_stands": 10
  }
]
```
### Get weather information
```http
GET /api/weather
```

## 📌 Contribution Guidelines
1. **Fork this repository**
2. **Create a new branch** (`git checkout -b feature-branch`)
3. **Commit your changes** (`git commit -m 'Add new feature'`)
4. **Push the branch** (`git push origin feature-branch`)
5. **Open a Pull Request**

## 📜 License
MIT License
