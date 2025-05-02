// Initial region mapping
const regionMapping = {
    'uz-ta': 'toshkent-oblast', // Tashkent City
    'uz-tk': 'toshkent-oblast', // Tashkent Region
    'uz-qa': 'kashkadarinskaya-oblast',
    'uz-ng': 'namanganskaya-oblast',
    'uz-an': 'andizhanskaya-oblast',
    'uz-bu': 'buharskaya-oblast',
    'uz-fa': 'ferganskaya-oblast',
    'uz-ji': 'dzhizakskaya-oblast',
    'uz-sa': 'samarkandskaya-oblast',
    'uz-si': 'syrdarinskaya-oblast',
    'uz-su': 'surhandarinskaya-oblast',
    'uz-qr': 'karakalpakstan',
    'uz-kh': 'horezmskaya-oblast',
    'uz-nw': 'navoijskaya-oblast'
};

let clickCounts = {};
let currentDataType = 'region'; // Track the current map context (region by default)

// Function to load Uzbekistan map
function loadUzbekistanMap() {
    currentDataType = 'region'; // Set map context to 'region'
    fetch('/api/listings-count-by-region/')
        .then(response => response.json())
        .then(data => {
            const chartData = Object.keys(data).map(region => {
                const hcKey = Object.keys(regionMapping).find(key => regionMapping[key] === region);
                return { 'hc-key': hcKey, value: data[region] };
            });

            const maxValue = Math.max(...Object.values(data));

            Highcharts.mapChart('container', {
                chart: { map: 'countries/uz/uz-all', height:600 },
                title: { text: 'Uzbekistan | Listing counts by region' },
                subtitle: { text: 'Double-click Tashkent for a detailed view!' },
                colorAxis: {
                    min: 1, max: maxValue, type: 'logarithmic',
                    stops: [
                        [0, '#0000FF'], [0.1, '#3366FF'], [0.2, '#3399FF'], [0.3, '#66B2FF'],
                        [0.4, '#99CCFF'], [0.5, '#FFFF00'], [0.6, '#FFCC33'], [0.7, '#FF9933'],
                        [0.8, '#FF6633'], [0.9, '#FF3333'], [1, '#FF0000']
                    ]
                },
                series: [{
                    name: '',
                    data: chartData,
                    joinBy: 'hc-key',
                    states: { hover: { color: '#a4edba' } },
                    dataLabels: { enabled: true, format: '{point.name}' },
                    point: {
                        events: {
                            click: function () {
                                const regionKey = this['hc-key'];
                                clickCounts[regionKey] = (clickCounts[regionKey] || 0) + 1;

                                if (regionKey === 'uz-ta' && clickCounts[regionKey] === 2) {
                                    clickCounts[regionKey] = 0;
                                    // Trigger API call with data_type=district


                                    loadTashkentMap();
                                    fetchDataAndUpdateBarChart({ data_type: 'district' });
                                    fetchRenderStreamGraph({ data_type: 'district' });

                                } else {
                                    filterByRegion(regionKey);
                                }
                            }
                        }
                    }
                }]
            });
        })
        .catch(error => { console.error('Error fetching data:', error); });
}

// Function to filter data by region when a region is clicked
function filterByRegion(regionKey) {
    const regionName = regionMapping[regionKey];

    if (!regionName) {
        console.error('Region not found in mapping:', regionKey);
        return;
    }

    let regionInput = document.querySelector('input[name="region"]');
    if (!regionInput) {
        regionInput = document.createElement('input');
        regionInput.type = 'hidden';
        regionInput.name = 'region';
        document.getElementById('filter-form').appendChild(regionInput);
    }
    regionInput.value = regionName;

    fetchDataAndAnimate();
}

// Fetch initial Uzbekistan map
loadUzbekistanMap();
