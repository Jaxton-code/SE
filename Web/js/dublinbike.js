$(document).ready(function () {
    let map;
    let markers = [];

    // 获取不同颜色的 Marker
    function getMarkerIcon(bikeCount) {
        if (bikeCount === 0) {
            return "http://maps.google.com/mapfiles/ms/icons/red-dot.png"; // 无车时红色
        } else if (bikeCount <= 4) {
            return "http://maps.google.com/mapfiles/ms/icons/yellow-dot.png"; // 车少时黄色
        } else {
            return "http://maps.google.com/mapfiles/ms/icons/green-dot.png"; // 车多时绿色
        }
    }

    // 初始化地图
    function initMap() {
        map = new google.maps.Map(document.getElementById("map"), {
            zoom: 13,
            center: { lat: 53.3498, lng: -6.2603 } // 都柏林中心位置
        });
        loadStations();  // 加载站点
        loadWeather();   // 加载天气
    }

    // 加载站点信息 (API: /api/stations)
    async function loadStations() {
        try {
            const response = await fetch('/api/stations'); // 通过后端 API 获取数据
            const stations = await response.json();

            markers.forEach(marker => marker.setMap(null)); // 清除旧标记
            markers = [];

            stations.forEach(station => {
                const marker = new google.maps.Marker({
                    position: { lat: station.position_lat, lng: station.position_lng },
                    map: map,
                    icon: getMarkerIcon(station.available_bikes),
                    title: station.name
                });

                // 点击标记显示站点详情
                marker.addListener('click', () => {
                    displayStationDetail(station);
                });

                markers.push(marker);
            });
        } catch (error) {
            console.error("Failed to load stations:", error);
        }
    }

    // 加载天气信息 (API: /api/weather)
    async function loadWeather() {
        try {
            const response = await fetch('/api/weather'); // 获取天气信息
            const weather = await response.json();

            // 更新天气信息到界面
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

    // 显示站点详情
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

    // 初始化地图
    initMap();
});
