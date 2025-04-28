// Function to fetch data and render streamgraph
function fetchRenderStreamGraph(filters) {
    const loadingAnimation = document.getElementById('loading-animation'); // Select the loading animation
    const chartContainer = document.getElementById('chart-container'); // Select the chart container

    // Show the loader and hide the chart
    loadingAnimation.style.display = 'block';
    chartContainer.style.display = 'none';

    const queryString = new URLSearchParams(filters).toString();
    fetch(`/api/monthly-average-price/?${queryString}`)
        .then(response => response.json())
        .then(data => {
            const regionMap = filters.data_type === 'district' ? {
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
            } : {
                'andizhanskaya-oblast': 'Andijan',
                'buharskaya-oblast': 'Bukhara',
                'dzhizakskaya-oblast': 'Jizzakh',
                'ferganskaya-oblast': 'Fergana',
                'horezmskaya-oblast': 'Khorezm',
                'karakalpakstan': 'Karakalpakstan',
                'kashkadarinskaya-oblast': 'Kashkadarya',
                'namanganskaya-oblast': 'Namangan',
                'navoijskaya-oblast': 'Navoi',
                'samarkandskaya-oblast': 'Samarkand',
                'surhandarinskaya-oblast': 'Surkhandarya',
                'syrdarinskaya-oblast': 'Sirdarya',
                'toshkent-oblast': 'Tashkent'
            };

            const seriesData = Object.keys(data).map(region => ({
                name: regionMap[region] || region,
                data: data[region].data.map(([month, value]) => ({
                    x: new Date(`${month}-01`).getTime(), // Ensure valid date format with "-01"
                    y: value
                }))
            }));

            Highcharts.chart('chart-container', {
                chart: {
                    type: 'streamgraph',
                    height: 600
                },
                title: {
                    text: filters.data_type === 'district' ?
                        'District Statistics | Monthly Average Prices' :
                        'Regional Statistics | Monthly Average Prices'
                },
                xAxis: {
                    type: 'datetime',
                    title: {
                        text: 'Time (Monthly)'
                    },
                    labels: {
                        format: '{value:%b %Y}' // Display month-year in tooltip
                    }
                },
                yAxis: {
                    title: {
                        text: 'Price (in million UZS)'
                    },
                    labels: {
                        enabled: false
                    }
                },
                legend: {
                    enabled: false
                },
                series: seriesData,
                tooltip: {
                    headerFormat: '<b>{series.name}</b><br>',
                    pointFormat: 'Month: {point.x:%B %Y}<br>Value: {point.y:.2f} million UZS'
                },
                plotOptions: {
                    series: {
                        label: {
                            connectorAllowed: false
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Error fetching data:', error))
        .finally(() => {
            // Hide the loader and show the chart
            loadingAnimation.style.display = 'none';
            chartContainer.style.display = 'block';
        });
}

// Fetch initial data without filters
fetchRenderStreamGraph({ data_type: 'region' });

// Event listener for filter changes
document.querySelectorAll('.filter').forEach(filterElement => {
    filterElement.addEventListener('change', function () {
        const filters = {};
        document.querySelectorAll('.filter').forEach(filter => {
            if (filter.value) {
                filters[filter.name] = filter.value;
            }
        });

        // Ensure data_type is preserved based on current context
        filters.data_type = currentDataType; // Use the global state variable

        // Fetch and render the streamgraph with the updated filters
        fetchRenderStreamGraph(filters);
    });
});

// Reset button functionality
document.getElementById('reset-button').addEventListener('click', function () {
    document.getElementById('filter-form').reset();
    fetchRenderStreamGraph({ data_type: currentDataType }); // Respect the current context when resetting
});
