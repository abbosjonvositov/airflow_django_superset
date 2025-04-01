// Function to fetch data and update chart
function fetchDataAndUpdateBarChart(filters) {
    const loadingAnimation = document.getElementById('loading-region-by-stat'); // Loader
    const chartContainer = document.getElementById('region-by-stat'); // Chart container

    // Show loader and hide chart
    loadingAnimation.style.display = 'block';
    chartContainer.style.display = 'none';

    const queryString = new URLSearchParams(filters).toString();
    fetch(`/api/by-region-stats/?${queryString}`)
        .then(response => response.json())
        .then(data => {
            const metrics = ['avg_price', 'avg_price_usd'];
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
            const regions = Object.keys(data).map(region => regionMap[region] || region);

            // Function to extract data for each metric
            function getMetricData(metric) {
                return Object.keys(data).map(region => data[region][metric]);
            }

            Highcharts.chart('region-by-stat', {
                chart: {
                    type: 'bar',
                    height: 600
                },
                title: {
                    text: filters.data_type === 'district' ?
                        'District Statistics | Analysis by District' :
                        'Regional Statistics | Analysis by Region'
                },
                xAxis: {
                    categories: regions,
                },
                yAxis: [{
                    // Primary yAxis for avg_price
                    title: {
                        text: 'Avg Price (in million UZS)'
                    },
                    min: 0,
                    opposite: true,
                    labels: {
                        format: '{value}'
                    }
                }, {
                    // Secondary yAxis for avg_price_usd
                    title: {
                        text: 'Avg Price (in thousand USD)'
                    },
                    min: 0,
                    opposite: false,
                    labels: {
                        format: '{value}'
                    }
                }],
                series: metrics.map(metric => ({
                    name: metric.replace(/_/g, ' ').toUpperCase(),
                    data: getMetricData(metric),
                    yAxis: metrics.indexOf(metric)
                }))
            });
        })
        .catch(error => console.error('Error fetching data:', error))
        .finally(() => {
            // Hide loader and show chart
            loadingAnimation.style.display = 'none';
            chartContainer.style.display = 'block';
        });
}

// Fetch initial data without filters
fetchDataAndUpdateBarChart({ data_type: 'region' });

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

        // Fetch and update the chart with the updated filters
        fetchDataAndUpdateBarChart(filters);
    });
});

// Reset button functionality
document.getElementById('reset-button').addEventListener('click', function () {
    document.getElementById('filter-form').reset();
    fetchDataAndUpdateBarChart({ data_type: currentDataType }); // Respect the current context when resetting
});
