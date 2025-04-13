
    let map;
    let markers = [];
    let userMarker = null;
    let trendChartInstance;
    let selectedStationNumber;
    let directionService;
    let directionsRenderer;


 
    console.log("JS loaded!");


    function getMarkerIcon(bikeCount) {
        if (bikeCount === 0) {
            return "http://maps.google.com/mapfiles/ms/icons/red-dot.png"; 
        } else if (bikeCount <= 4) {
            return "http://maps.google.com/mapfiles/ms/icons/yellow-dot.png"; 
        } else {
            return "http://maps.google.com/mapfiles/ms/icons/green-dot.png"; 
        }
    }

    function initMap() {
        map = new google.maps.Map(document.getElementById("map"), {
            zoom: 13,
            center: { lat: 53.3498, lng: -6.2603 }
        });
        directionService = new google.maps.DirectionsService();
        directionsRenderer = new google.maps.DirectionsRenderer({ suppressMarkers: true});
        directionsRenderer.setMap(map)
        loadStations();

        loadWeather();
        // getLocation();  // Automatically find user location when the map loads

        setInterval(loadWeather, 3600000);  // Refresh weather every hour
        setInterval(loadStations, 60000);  // Refresh stations every minute
    }

    window.initMap = initMap;

    function drawRouteToStation (stationLat , stationLng){
        if (!userMarker){
            alert("User location not found")
            return;
        
        }
        const origin = userMarker.getPosition();
        const destination = new google.maps.LatLng(stationLat,stationLng);

        const request = {
            origin: origin,
            destination: destination,
            travelMode: google.maps.TravelMode.WALKING

        }

        directionService.route(request, function(result, status) {
            if (status === google.maps.DirectionsStatus.OK) {
                directionsRenderer.setDirections(result);
            } else {
                console.error("Directions request failed due to " + status);
            }
        });

        setTimeout(() => {
            $('#cyclist').css('animation', 'cycleIn 3s ease-out forwards');
        }, 300); // delay 0.3s
        
    
     
    }
    


    let stations = []
    async function loadStations() {
        try {
            const response = await fetch('/api/stations');
            stations = await response.json();

            markers.forEach(marker => marker.setMap(null)); 
            markers = [];

            stations.forEach(station => {
                const marker = new google.maps.Marker({
                    position: { lat: station.position_lat, lng: station.position_lng },
                    map: map,
                    icon: getMarkerIcon(station.available_bikes),
                    title: station.name
                });

                marker.addListener('click', () => {
                    displayStationDetail(station);
                });

                markers.push(marker);
            });

            getLocation();
        } catch (error) {
            console.error("Failed to load stations:", error);
        }
    }

    async function loadWeather() {
        try {
            const response = await fetch('/api/weather');
            const weather = await response.json();

            $('#temp').text(`${weather.temp}°C`);
            $('#tempFeel').text(`${weather.temp_feel}°C`);
            $('#condition').text(weather.weather_main);
            $('#wind').text(`${weather.wind_speed} m/s`);
            $('#clouds').text(`${weather.clouds}%`);
            $('#sunrise').text(weather.sunrise);
            $('#sunset').text(weather.sunset);
        } catch (error) {
            console.error("Failed to load weather:", error);
        }
    }

    function displayStationDetail(station) {
        console.log("Station clicked:", station.name);
        selectedStationNumber = station.number;
        
        
        $('#stationDetail').html(`
            <div class="station-detail-card">
                <h3>${station.name}</h3>
                <p><strong>Address:</strong> ${station.address}</p>
                <p><strong>Bikes Available:</strong> ${station.available_bikes}</p>
                <p><strong>Stands Available:</strong> ${station.available_bike_stands}</p>
                <p><strong>Status:</strong> ${station.status}</p>
                <p><strong>Location:</strong> (${station.position_lat}, ${station.position_lng})</p>

                <div style="margin-top: 10px; border-top: 1px solid #ccc; padding-top: 10px;">
                <label for="predictTime">Select Future Time:</label>
                <input type="datetime-local" id="predictTime">
                <button id="predictBtn">Predict Availability</button>
                <p id="predictOutput"></p>

               </div>
            </div>
        `);
        map.setCenter({ lat: station.position_lat, lng: station.position_lng });
        loadTrendChart(station.name);


        const predictBtn = document.getElementById("predictBtn");
        const timeInput = document.getElementById("predictTime");
        const output = document.getElementById("predictOutput");
        
        if (!timeInput || !output || !predictBtn) {
            console.error(" DOM elements for prediction not found.");
            return;
        }
        
        predictBtn.addEventListener("click", () => {
            const datetime = timeInput.value.replace("T", " ");
            console.log("Predicting for", selectedStationNumber, datetime);
        
            if (!datetime || !selectedStationNumber) {
                output.innerText = "Please select a time.";
                return;
            }
        
            fetch(`/predict?station_number=${selectedStationNumber}&datetime=${encodeURIComponent(datetime)}`)
                .then(res => res.json())
                .then(data => {
                    if (data.prediction !== undefined) {
                        // ✅ Use backticks here for interpolation
                        output.innerText = `🚲 Predicted bikes at ${data.datetime}: ${data.prediction}`;
                    } else {
                        output.innerText = "Prediction failed.";
                    }
                })
                .catch(err => {
                    console.error("Prediction error:", err);
                    output.innerText = "Error getting prediction.";
                });
        }); 
        drawRouteToStation(station.position_lat, station.position_lng);

    }


    function displayNearestStationDetail(station ,distance) {
        $('#stationDetail').html(`
            <div class="station-detail-card">
                <h3>${station.name} <br> This is your nearest Bike Station! </br> </h3>
                <p><strong>Address:</strong> ${station.address}</p>
                <p><strong>Bikes Available:</strong> ${station.available_bikes}</p>
                <p><strong>Stands Available:</strong> ${station.available_bike_stands}</p>
                <p><strong>Status:</strong> ${station.status}</p>
                <p><strong>Location:</strong> (${station.position_lat}, ${station.position_lng})</p>
                <p><strong> Distance:</strong> ${distance.toFixed(2)} km</p>
            </div>
        `);
        map.setCenter({ lat: station.position_lat, lng: station.position_lng });
    }
    function getLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                showPosition, 
                showError, 
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
            );
        } else {
            console.error("Geolocation is not supported by this browser.");
        }
    }
    function showPosition(position) {
        console.log("showPosition() called with:", position.coords);
        const userLat = position.coords.latitude;
        const userLong = position.coords.longitude;
        console.log("User Location: ", userLat, userLong);

        if (userMarker){
            userMarker.setPosition({lat: userLat, lng: userLong});
        } else {
            userMarker = new google.maps.Marker({
                position: { lat: userLat, lng: userLong },
                map: map,
                icon: {
                    url: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
                    scaledSize: new google.maps.Size(40, 40)
                },
                title: "Your Location",
                zIndex: 1000 // Make sure user marker appears above other markers
            });
        }

        findNearestStation(userLat, userLong);
    }

    function showError(error) {
        switch (error.code) {
            case error.PERMISSION_DENIED:
                console.error("User denied the request for Geolocation.");
                break;
            case error.POSITION_UNAVAILABLE:
                console.error("Location information is unavailable.");
                break;
            case error.TIMEOUT:
                console.error("The request to get user location timed out.");
                break;
            default:
                console.error("An unknown error occurred.");
                break;
        }
    }

    function getDistance(lat1, lng1, lat2, lng2) {
        const R = 6371; 
        const dLat = (lat2 - lat1) * (Math.PI / 180);
        const dLng = (lng2 - lng1) * (Math.PI / 180);
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLng / 2) * Math.sin(dLng / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    }

    function findNearestStation(userLat, userLong) {
        console.log(" findNearestStation() called with:", userLat, userLong);
        console.log(" Checking against", markers.length, "station markers");
        let nearestStation = null;
        let minDistance = Infinity;
        let nearestStationData = null;

        markers.forEach( marker => {
            const stationLat = marker.getPosition().lat();
            const stationLng = marker.getPosition().lng();
            const distance = getDistance(userLat, userLong, stationLat, stationLng);

            if (distance < minDistance) {
                minDistance = distance;
                nearestStation = marker;

                nearestStationData = stations.find(station =>
                station.position_lat === stationLat &&
                station.position_lng === stationLng
                );
                
            }
        });

        if (nearestStation) {
            console.log("Nearest Station:", nearestStation.getTitle());
            map.setCenter(nearestStation.getPosition());
            nearestStation.setAnimation(google.maps.Animation.BOUNCE);
            displayNearestStationDetail(nearestStationData, minDistance)
            loadTrendChart(nearestStationData.name);
        }  else {
            console.log(" No nearest station found.");
        }
    }


      async function loadTrendChart(stationName) {
        console.log("Chart triggered for:", stationName);
        try {
            const response = await fetch(`/api/trend/${stationName}`);
            const trend = await response.json();
    
            if (!trend || trend.length === 0) {
                console.warn("No trend data to display.");
                return;
            }
            
            const labels = trend.map(entry => entry.timestamp);
            const values = trend.map(entry => entry.available_bikes);
            const ctx = document.getElementById('trendChart').getContext('2d');
    
            // Destroy old chart instance if it exists
            if (trendChartInstance) {
                trendChartInstance.destroy();
            }
    
            // Create new chart
            trendChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: `Available Bikes (${stationName})`,
                        data: values,
                        fill: true,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.3,
                        pointRadius: 3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: .8,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Bikes Available'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Time (past 24h)'
                            },
                            ticks: {
                                maxTicksLimit: 10
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: true
                        }
                    }
                }
            });
    
        } catch (error) {
            console.error("Failed to load trend chart:", error);
        }
    }
  