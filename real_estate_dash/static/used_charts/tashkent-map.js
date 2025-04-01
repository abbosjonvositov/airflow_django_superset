function loadTashkentMap(selectedDistrict = null) {
    currentDataType = 'district'; // Set map context to 'district'
    Promise.all([
        fetch('/get-geojson/').then(response => response.json()),
        fetch('/api/districts-count/?region_name=toshkent-oblast').then(response => response.json())
    ])
    .then(([geojson, districtData]) => {
        let processedFeatures = [];

        // Mapping dictionary: API response -> GeoJSON district names
        const districtMapping = {
            'Алмазарский район': 'Almazar',
            'Бектемирский район': 'Bektemir',
            'Мирабадский район': 'Mirabad',
            'Мирзо-Улугбекский район': 'Mirzo Ulugbek',
            'Сергелийский район': 'Sergeli',
            'Учтепинский район': 'Uchtepa',
            'Чиланзарский район': 'Chilanzar',
            'Шайхантахурский район': 'Shaykhantokhur',
            'Юнусабадский район': 'Yunusabad',
            'Яккасарайский район': 'Yakkasaray',
            'Яшнабадский район': 'Yashnobod'
        };

        // Filter districtData if a district is selected
        if (selectedDistrict) {
            districtData = Object.fromEntries(
                Object.entries(districtData).filter(([key]) => districtMapping[key] === selectedDistrict)
            );
        }

        // Process GeoJSON features
        geojson.features.forEach(feature => {
            if (feature.geometry.geometries) {
                feature.geometry.geometries.forEach(geom => {
                    processedFeatures.push({
                        type: "Feature",
                        properties: feature.properties,
                        geometry: geom
                    });
                });
            } else {
                processedFeatures.push(feature);
            }
        });

        // Convert GeoJSON to Highcharts format
        const states = Highcharts.geojson({
            type: "FeatureCollection",
            features: processedFeatures
        }, 'map');

        // Assign values and colors based on districtData
        states.forEach(state => {
            let districtName = state.properties.name;
            let originalName = Object.keys(districtMapping).find(key => districtMapping[key] === districtName);
            let count = districtData[originalName] || 0; // Default to 0 if no data

            state.value = count; // Assign value for choropleth mapping
        });

        // Highcharts Map Configuration
        Highcharts.mapChart('container', {
            chart: { map: geojson },
            title: { text: 'Tashkent City Districts - Count Visualization' },
            subtitle: { text: 'Right-click to go back to Uzbekistan map.' },
            mapNavigation: {
                enabled: true,
                buttonOptions: { verticalAlign: 'bottom' }
            },
            colorAxis: {
                min: Math.min(...Object.values(districtData)),
                max: Math.max(...Object.values(districtData)),
                stops: [
                    [0, '#EFEFFF'], [0.1, '#3366FF'], [0.2, '#3399FF'], [0.3, '#66B2FF'],
                    [0.4, '#99CCFF'], [0.5, '#FFFF00'], [0.6, '#FFCC33'], [0.7, '#FF9933'],
                    [0.8, '#FF6633'], [0.9, '#FF3333'], [1, '#FF0000']
                ]
            },
            series: [{
                name: 'Districts',
                data: states.map(state => ({
                    name: state.properties.name,
                    value: state.value
                })),
                joinBy: ['name', 'name'], // Ensure proper joining
                states: { hover: { color: Highcharts.getOptions().colors[4] } },
                dataLabels: {
                    enabled: true,
                    format: '{point.name}', // Only district name
                    style: {
                        fontWeight: 'bold',
                        color: '#333333', // Distinct label color
                        textOutline: 'none'
                    }
                },
                tooltip: {
                    headerFormat: '',
                    pointFormat: '<b>{point.name}</b>: {point.value}' // Show count on hover
                },
                point: {
                    events: {
                        click: function () {
                            const clickedDistrict = this.name;
                            filterByDistrict(clickedDistrict);
                        }
                    }
                }
            }]
        });

        // Add filter dynamically after the Tashkent map is loaded
//        const form = document.getElementById('filter-form'); // Assuming a form exists with this ID
//        let dataTypeInput = document.querySelector('input[name="data_type"]');
//        if (!dataTypeInput) {
//            dataTypeInput = document.createElement('input');
//            dataTypeInput.type = 'hidden'; // Hidden input if necessary
//            dataTypeInput.name = 'data_type';
//            dataTypeInput.value = 'district'; // Set to 'district'
//            form.appendChild(dataTypeInput);
//        }

        // Right-click to go back to Uzbekistan map
        const container = document.getElementById('container');
        if (!container.getAttribute('data-listener-added')) {
            container.addEventListener('contextmenu', function (event) {
                event.preventDefault(); // Prevent default right-click menu

                // Clear the district filter before navigating back to Uzbekistan
                const districtInput = document.querySelector('input[name="district"]');
                if (districtInput) {
                    districtInput.remove(); // Remove the district input field
}



                // Reset the bar chart to regional data
                fetchDataAndUpdateBarChart({ data_type: 'region' });
                fetchRenderStreamGraph({ data_type: 'region' });

//                // Clear the district filter before navigating back to Uzbekistan
//                const districtInput = document.querySelector('input[name="district"]');
//                if (districtInput) {
//                    form.removeChild(districtInput);
//                }

                // Remove 'district' from the URL query parameters
                const fetchParams = new URLSearchParams(window.location.search);
                fetchParams.delete('district');
                const newUrl = window.location.pathname;
                window.history.replaceState(null, '', newUrl);

                loadUzbekistanMap();
            });

            container.setAttribute('data-listener-added', true);
        }
    })
    .catch(error => {
        console.error("Error loading or processing data:", error);
    });
}

let isFetching = false;

function fetchDataAndUpdateBarChart(filters) {
    if (isFetching) return; // Exit if a fetch is already in progress
    isFetching = true;

    fetch(`/api/by-region-stats/?${new URLSearchParams(filters)}`)
        .then(response => response.json())
        .then(data => {
            // Update the chart with the fetched data
            updateChart(data);
        })
        .catch(error => console.error("Error fetching data:", error))
        .finally(() => { isFetching = false; }); // Reset fetch state
}

function fetchRenderStreamGraph(filters) {
    if (isFetching) return; // Exit if a fetch is already in progress
    isFetching = true;

    fetch(`/api/monthly-average-price/?${new URLSearchParams(filters)}`)
        .then(response => response.json())
        .then(data => {
            // Update the chart with the fetched data
            updateChart(data);
        })
        .catch(error => console.error("Error fetching data:", error))
        .finally(() => { isFetching = false; }); // Reset fetch state
}



// Function to filter data when a district is clicked
function filterByDistrict(districtName) {
    console.log('filterByDistrict triggered with:', districtName);

    let districtInput = document.querySelector('input[name="district"]');
    if (!districtInput) {
        districtInput = document.createElement('input');
        districtInput.type = 'hidden';
        districtInput.name = 'district';
        document.getElementById('filter-form').appendChild(districtInput);
    }
    districtInput.value = districtName; // Directly use the districtName from the map

    fetchDataAndAnimate(); // Trigger your data fetch and animation
}
