import sys
import os
from real_estate_dashapp.models import (
    LayoutDim, FoundationDim, WCDim, DimCharacteristic,
    CityDim, DistrictDim, LatLonDim, DimLocation, DimNumeric,
    DimTime, FactApartments, RepairDim, RegionDim, ExchangeRateDim, ETLLog
)

# Set Django project path and settings
sys.path.append("/opt/airflow/django_project")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "real_estate_dash.settings")

import django

django.setup()

from datetime import datetime
import pytz
from pprint import pprint

def add_timezone(dt):
    if isinstance(dt, str):
        dt = datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%fZ')

    # Set dt as UTC first
    dt = dt.replace(tzinfo=pytz.utc)

    # Convert to Asia/Tashkent
    tashkent_tz = pytz.timezone('Asia/Tashkent')
    return dt.astimezone(tashkent_tz)


def load_data(ti):
    all_data = ti.xcom_pull(task_ids='transform_data')  # Task ID for OLX
    pprint(all_data)
    try:
        for index, row in enumerate(all_data):
            print(row['city_name'])
            # Sync ORM methods
            city_dim, created_city = CityDim.objects.using('default').get_or_create(city_name=row.get('city_name'))
            region_dim, created_region = RegionDim.objects.using('default').get_or_create(
                region_name=row['region_name']
            )
            district_dim, created_district = DistrictDim.objects.using('default').get_or_create(
                district_name=row['district_name']
            )
            lat_lon_dim, created_lat_lon = LatLonDim.objects.using('default').get_or_create(
                latitude=row['latitude'], longitude=row['longitude']
            )

            location, created_location = DimLocation.objects.using('default').get_or_create(
                city=city_dim,
                region=region_dim,
                district=district_dim,
                lat_lon=lat_lon_dim
            )

            numeric, created_numeric = DimNumeric.objects.using('default').get_or_create(
                total_area=row['total_area'],
                number_of_rooms=row['number_of_rooms'],
                floors=row['floor'],
                total_floors=row['total_floors'],
                price_per_sqm=row['price_per_sqm'],
                price=row['price']
            )

            layout_dim, created_layout = LayoutDim.objects.using('default').get_or_create(
                layout_name=row['layout_name']
            )
            foundation_dim, created_foundation = FoundationDim.objects.using('default').get_or_create(
                foundation_name=row['foundation_name']
            )
            wc_dim, created_wc = WCDim.objects.using('default').get_or_create(
                wc_name=row['wc_name']
            )
            repair_dim, created_repair = RepairDim.objects.using('default').get_or_create(
                repair_name=row['repair_name']
            )

            characteristic, created_characteristic = DimCharacteristic.objects.using('default').get_or_create(
                type_of_market=row['type_of_market_key'],
                is_furnished=row['is_furnished'],
                year_of_construction=row['year_of_construction'],
                layout=layout_dim,
                foundation=foundation_dim,
                wc=wc_dim,
                repair=repair_dim
            )

            # Time dimension (sync)
            time_dim, created_time = DimTime.objects.using('default').get_or_create(
                datetime=add_timezone(row['last_refresh_time']),
                defaults={
                    'year': add_timezone(row['last_refresh_time']).year,
                    'month': add_timezone(row['last_refresh_time']).month,
                    'day': add_timezone(row['last_refresh_time']).day,
                    'week': add_timezone(row['last_refresh_time']).isocalendar()[1],
                    'weekday': add_timezone(row['last_refresh_time']).strftime('%A')
                }
            )

            # Update or create the fact table (sync)
            FactApartments.objects.using('default').update_or_create(
                apartment_id=row['id'],
                defaults={
                    'time': time_dim,
                    'location': location,
                    'numeric': numeric,
                    'characteristic': characteristic
                }
            )

    except Exception as e:
        raise RuntimeError(f"❌ Error loading data: {e}")
