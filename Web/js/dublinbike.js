$(document).ready(function () {
    let map;
    let markers = [];

    // Get marker icon based on number of available bikes
    function getMarkerIcon(bikeCount) {
        if (bikeCount === 0) {
            return "http://maps.google.com/mapfiles/ms/icons/red-dot.png"; // Red when no bikes
        } else if (bikeCount <= 4) {
            return "http://maps.google.com/mapfiles/ms/icons/yellow-dot.png"; // Yellow when few bikes
        } else {
            return "http://maps.google.com/mapfiles/ms/icons/green-dot.png"; // Green when many bikes
        }
    }

    // Initialize the map
    function initMap() {
        map = new google.maps.Map(document.getElementById("map"), {
            zoom: 13,
            center: { lat: 53.3498, lng: -6.2603 } // Dublin city center
        });
        loadStations();  // Load station data
        loadWeather();   // Load weather data
    }

    // Load station data from API (API: /api/stations)
    async function loadStations() {
        try {
            const response = await fetch('/api/stations'); // Fetch data from backend API
            const stations = await response.json();

            markers.forEach(marker => marker.setMap(null)); // Clear old markers
            markers = [];

            stations.forEach(station => {
                const marker = new google.maps.Marker({
                    position: { lat: station.position_lat, lng: station.position_lng },
                    map: map,
                    icon: getMarkerIcon(station.available_bikes),
                    title: station.name
                });

                // Show station details when marker is clicked
                marker.addListener('click', () => {
                    displayStationDetail(station);
                });

                markers.push(marker);
            });
        } catch (error) {
            console.error("Failed to load stations:", error);
        }
    }

    // Load weather data from API (API: /api/weather)
    async function loadWeather() {
        try {
            const response = await fetch('/api/weather'); // Fetch weather data
            const weather = await response.json();

            // Update weather info on the interface
            $('#temp').text(`${weather.temp}°C`);
            $('#tempFeel').text(`${weather.temp_feel}°C`);
            $('#condition').text(weather.weather_main);
            $('#wind').text(`${weather.wind_speed} m/s`);
            $('#clouds').text(`${weather.clouds}%`);
            $('#sunrise').text(new Date(weather.sunrise).toLocaleTimeString());
            $('#sunset').text(new Date(weather.sunset).toLocaleTimeString());

        } catch (error) {
            console.error("Failed to load weather:", error);
        }
    }

    // Display selected station details
    function displayStationDetail(station) {
        $('#stationDetail').html(`
            <div class="station-detail-card">
                <h3>${station.name}</h3>
                <p><strong>Address:</strong> ${station.address}</p>
                <p><strong>Bikes Available:</strong> ${station.available_bikes}</p>
                <p><strong>Stands Available:</strong> ${station.available_bike_stands}</p>
                <p><strong>Status:</strong> ${station.status}</p>
                <p><strong>Location:</strong> (${station.position_lat}, ${station.position_lng})</p>
            </div>
        `);
        map.setCenter({ lat: station.position_lat, lng: station.position_lng });
    }

    // Call map initializer
    initMap();
});
