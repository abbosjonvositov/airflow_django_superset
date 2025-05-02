import asyncssh
import aiomysql
import asyncio
from django.core.management.base import BaseCommand
from real_estate_dashapp.models import (
    LayoutDim, FoundationDim, WCDim, DimCharacteristic,
    CityDim, DistrictDim, LatLonDim, DimLocation, DimNumeric,
    DimTime, FactApartments, RepairDim, RegionDim, ExchangeRateDim, ETLLog
)

from django.db.models import Max
from datetime import datetime
from asgiref.sync import async_to_sync, sync_to_async
from pytz import timezone
import requests
import pytz
import os
import pandas as pd
from django.conf import settings
from django.utils.timezone import now

SSH_CONFIG = {
    "ssh_address": "ssh.pythonanywhere.com",
    "ssh_port": 22,
    "ssh_username": "gullolacorp",
    "ssh_password": "iambadguy571",
    "remote_bind_address": "gullolacorp.mysql.pythonanywhere-services.com",
    'remote_bind_port': 3306
}

MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "user": "gullolacorp",
    "password": "iambadguy571",
    "db": "gullolacorp$default",
    "port": 3306,
    "connect_timeout": 60
}

mapping_dict_regions = {
    "город Ташкент": "toshkent-oblast",
    "Ташкентская область": "toshkent-oblast",
    "Самаркандская область": "samarkandskaya-oblast",
    "Навоийская область": "navoijskaya-oblast",
    "Джизакская область": "dzhizakskaya-oblast",
    "Бухарская область": "buharskaya-oblast",
    "Наманганская область": "namanganskaya-oblast",
    "Сурхандарьинская область": "surhandarinskaya-oblast",
    "Республика Каракалпакстан": "karakalpakstan",
    "Ферганская область": "ferganskaya-oblast",
    "Сырдарьинская область": "syrdarinskaya-oblast",
    "Кашкадарьинская область": "kashkadarinskaya-oblast",
    "Андижанская область": "andizhanskaya-oblast",
    "Хорезмская область": "horezmskaya-oblast",
}

mapping_dict_repairs = {
    "evro": "Евроремонт",
    "custom": "Авторский проект",
    "sredniy": "Средний",
    "kapital": "Требует ремонта",
    "chernovaya": "Черновая отделка",
    "predchistovaya": "Предчистовая отделка"
}

mapping_dict_foundation = {
    "kirpich": "Кирпичный",
    "panel": "Панельный",
    "other": "Другие",
    "monolit": "Монолитный",
    "blok": "Блочный"
}

mapping_dict_district = {
    "Мирабадский район": "Мирабадский район",
    "Яккасарайский район": "Яккасарайский район",
    "Мирзо-Улугбекский район": "Мирзо-Улугбекский район",
    "Юнусабадский район": "Юнусабадский район",
    "Яшнободский район": "Яшнабадский район",
    "Сергелийский район": "Сергелийский район",
    "Учтепинский район": "Учтепинский район",
    "Шайхантахурский район": "Шайхантахурский район",
    "Чиланзарский район": "Чиланзарский район",
    "Алмазарский район": "Алмазарский район",
    "Бектемирский район": "Бектемирский район",
}


def add_timezone(dt):
    if isinstance(dt, str):
        dt = datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%fZ')

    # Set dt as UTC first
    dt = dt.replace(tzinfo=pytz.utc)

    # Convert to Asia/Tashkent
    tashkent_tz = pytz.timezone('Asia/Tashkent')
    return dt.astimezone(tashkent_tz)


def get_exchange_rate():
    cbu_rate_url = 'https://cbu.uz/oz/arkhiv-kursov-valyut/json/'
    response = requests.get(url=cbu_rate_url).json()[0]

    date_str, rate = response['Date'], float(response['Rate'])

    # Convert string to datetime object
    date = datetime.strptime(date_str, '%d.%m.%Y')

    return date, rate


def clean_numbers(value):
    if isinstance(value, str):
        if value.endswith('+'):
            return int(value[:-1])  # Convert '6+' → 6
        if value.isdigit():
            return int(value)
    elif isinstance(value, (int, float)):
        return int(value)  # Convert float-like values safely
    return 0  # Return None for invalid values


def map_value(mapping_dict, key):
    return mapping_dict.get(key, key)


class Command(BaseCommand):
    help = "Extract, Transform, and Load OLX data into the local SQLite3 database"

    @async_to_sync
    async def handle(self, *args, **kwargs):
        try:
            async with asyncssh.connect(
                    SSH_CONFIG["ssh_address"],
                    port=SSH_CONFIG["ssh_port"],
                    username=SSH_CONFIG["ssh_username"],
                    password=SSH_CONFIG["ssh_password"],
                    known_hosts=None
            ) as conn:
                self.stdout.write(self.style.SUCCESS("🔗 SSH Tunnel established!"))

                forwarder = await conn.forward_local_port(
                    listen_host="127.0.0.1",
                    listen_port=0,
                    dest_host=SSH_CONFIG["remote_bind_address"],
                    dest_port=SSH_CONFIG["remote_bind_port"]
                )
                # print(f"Forwarder: {forwarder}")

                MYSQL_CONFIG["port"] = forwarder.get_port()
                self.stdout.write(self.style.SUCCESS(f"🔍 Local tunnel created on port {MYSQL_CONFIG['port']}"))
                self.stdout.write(self.style.SUCCESS("🔍 Starting extract_and_load process..."))

                await self.extract_and_load()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ SSH Tunnel Error: {e}"))

    async def extract_and_load(self):
        etl_log = await sync_to_async(ETLLog.objects.using('default').create)(start_time=now(), status='Started')
        extracted_counts = {}
        # loaded_counts = {}
        # olx_count, uybor_count, flat_file_count = 0, 0, 0
        # Extract data from API
        try:
            date, usd_uzs_rate = get_exchange_rate()

            await sync_to_async(ExchangeRateDim.objects.using('default').create)(
                datetime=add_timezone(date),
                usd_uzs_rate=usd_uzs_rate
            )
            self.stdout.write(self.style.SUCCESS('✅ Exchange rate updated'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Exchange rate: {e}"))

        conn = None
        cursor = None

        # Extract data from Database
        try:
            etl_log.status = 'Extract'
            await sync_to_async(etl_log.save)()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.stdout.write(self.style.SUCCESS("🔌 Connecting to MySQL database..."))
            conn = await aiomysql.connect(loop=loop, **MYSQL_CONFIG)
            # print(f"Connection object: {conn}")
            if conn is None:
                self.stdout.write(self.style.ERROR("❌ Failed to connect to MySQL database"))
                return

            cursor = await conn.cursor(aiomysql.DictCursor)
            print(f"Cursor object: {cursor}")
            if cursor is None:
                self.stdout.write(self.style.ERROR("❌ Failed to create MySQL cursor"))
                return
            self.stdout.write(self.style.SUCCESS('✅ Connected to MySQL database successfully!'))

            self.stdout.write(self.style.SUCCESS("🕵️ Fetching latest timestamp from SQLite3..."))

            latest_time_entry_olx = await sync_to_async(
                DimTime.objects.using('default').filter(factapartments__apartment_id__startswith='O').aggregate)(
                Max('datetime'))
            latest_timestamp_olx = latest_time_entry_olx['datetime__max'] or datetime(2000, 1, 1)
            self.stdout.write(self.style.SUCCESS(f"📅 Latest OLX timestamp: {latest_timestamp_olx}"))

            latest_time_entry_uybor = await sync_to_async(
                DimTime.objects.using('default').filter(factapartments__apartment_id__startswith='U').aggregate)(
                Max('datetime'))
            latest_timestamp_uybor = latest_time_entry_uybor['datetime__max'] or datetime(2000, 1, 1)
            self.stdout.write(self.style.SUCCESS(f"📅 Latest Uybor timestamp: {latest_timestamp_uybor}"))

            self.stdout.write(self.style.SUCCESS("📥 Fetching new records from OLX and Uybor concurrently..."))

            await cursor.execute("""
                SELECT
                    id, last_refresh_time, total_area_key AS total_area, number_of_rooms_key AS number_of_rooms,
                    floor_key AS floor, total_floors_key AS total_floors,
                    price / NULLIF(total_area_key, 0) AS price_per_sqm, price, type_of_market_key,
                    furnished_label AS is_furnished, year_of_construction_sale_key AS year_of_construction,
                    layout_label AS layout_name, house_type_label AS foundation_name, wc_label AS wc_name,
                    location_city_normalized_name AS city_name, location_district_name AS district_name,
                    map_lat AS latitude, map_lon AS longitude, repairs_label AS repair_name,
                    location_region_normalized_name AS region_name
                FROM olx_data
                WHERE last_refresh_time > %s
                ORDER BY last_refresh_time ASC;
            """, (latest_timestamp_olx,))
            olx_data = await cursor.fetchall()
            extracted_counts["OLX"] = len(olx_data)
            self.stdout.write(self.style.SUCCESS(f"✅ Fetched {len(olx_data)} OLX records."))

            await cursor.execute("""
                SELECT id, updatedAt AS last_refresh_time, square AS total_area, room AS number_of_rooms,
                    floor, floorTotal AS total_floors, priceEquivalent / NULLIF(square, 0) AS price_per_sqm,
                    priceEquivalent AS price,
                    CASE WHEN isNewBuilding = 'True' THEN 'primary' ELSE 'secondary' END AS type_of_market_key,
                    foundation AS foundation_name, region_name_ru AS region_name, district_name_ru AS district_name,
                    lat AS latitude, lng AS longitude, repair AS repair_name
                FROM uybor_data
                WHERE operationType = 'sale' AND updatedAt > %s
                ORDER BY updatedAt ASC;
            """, (latest_timestamp_uybor,))
            uybor_data = await cursor.fetchall()
            extracted_counts["Uybor"] = len(uybor_data)
            self.stdout.write(self.style.SUCCESS(f"✅ Fetched {len(uybor_data)} Uybor records."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error during fetching data: {e}"))

        # Extract data from Flat files
        try:
            file_path = os.path.join(settings.MEDIA_ROOT, "cleaned_data.xlsx")

            if not os.path.exists(file_path):
                self.stdout.write(self.style.WARNING(f"⚠️ Flat file not found: {file_path}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"📂 Loading data from flat file: {file_path}"))

                df = await sync_to_async(pd.read_excel, thread_sensitive=True)(file_path)

                required_columns = {
                    "id", "last_refresh_time", "total_area", "number_of_rooms", "floor",
                    "total_floors", "price_per_sqm", "price", "type_of_market_key",
                    "foundation_name", "region_name", "district_name", "latitude",
                    "longitude", "repair_name"
                }

                df['last_refresh_time'] = pd.to_datetime(df['last_refresh_time'], errors="coerce")
                df['price_per_sqm'] = df['price'] / df['total_area']
                df[df.select_dtypes(include=['float', 'float32', 'float64']).columns] = df.select_dtypes(
                    include=['float', 'float32', 'float64']).fillna(0)
                df[df.select_dtypes(include=['object']).columns] = df.select_dtypes(
                    include=['object']).fillna('Unknown')

                # Fetch existing apartment IDs and remove 'F' prefix
                existing_apartment_ids = await sync_to_async(
                    lambda: {ap_id[1:] for ap_id in FactApartments.objects.values_list("apartment_id", flat=True) if
                             ap_id.startswith("F")},
                    thread_sensitive=True
                )()

                # Filter out rows where the 'id' already exists in DB (after removing 'F' prefix)
                df_filtered = df[~df['id'].astype(str).isin(existing_apartment_ids)]

                missing_columns = required_columns - set(df.columns)
                if missing_columns:
                    self.stdout.write(self.style.ERROR(f"❌ Missing columns in flat file: {missing_columns}"))

                flat_data = df_filtered.to_dict(orient="records")
                self.stdout.write(self.style.SUCCESS(f"✅ Loaded {len(flat_data)} new records from flat file."))

                extracted_counts["FlatFile"] = len(flat_data)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error loading flat file: {e}"))


        finally:
            try:
                print("Attempting to close cursor...")
                if cursor is not None:
                    await cursor.close()
                    print("Cursor closed")
                else:
                    print("Cursor was None")
            except Exception as e:
                print(f"Error closing cursor: {e}")

            try:
                print("Attempting to close connection...")
                if conn is not None:
                    await conn.ensure_closed()
                    print("Connection closed")
                else:
                    print("Connection was None")
            except Exception as e:
                print(f"Error closing connection: {e}")

        etl_log.extracted_data = extracted_counts
        etl_log.total_extracted = sum(extracted_counts.values())
        await sync_to_async(etl_log.save)()

        # Merge data from all sources
        all_data = [
                       {**row, 'id': f"O{row['id']}"} for row in olx_data if 'id' in row
                   ] + [
                       {**row, 'id': f"U{row['id']}"} for row in uybor_data if 'id' in row
                   ] + [
                       {**row, 'id': f"F{row['id']}"} for row in flat_data if 'id' in row
                   ]

        if not all_data:
            self.stdout.write(self.style.SUCCESS("✅ No new data to insert."))
            return

        try:
            olx_loaded_count = 0
            uybor_loaded_count = 0
            flat_loaded_count = 0
            # olx_loaded = []
            # uybor_loaded = []
            # flat_loaded = []
            etl_log.status = 'Load'
            await sync_to_async(etl_log.save)()
            for index, row in enumerate(all_data):

                loaded_counts = etl_log.loaded_data or {'OLX': 0, 'Uybor': 0, 'FlatFile': 0}

                if 'id' not in row:
                    self.stdout.write(self.style.ERROR(f"❌ Error processing data: Missing 'id' in record {index + 1}"))
                    continue

                # self.stdout.write(self.style.SUCCESS(f"🔄 Processing record {index + 1}/{len(all_data)}..."))

                # Set default values for missing fields
                row = {key: (value if value is not None else default_value) for key, value, default_value in [
                    ('city_name', row.get('city_name', 'Unknown'), 'Unknown'),
                    ('region_name', row.get('region_name', 'Unknown'), 'Unknown'),
                    ('district_name', row.get('district_name', 'Unknown'), 'Unknown'),
                    ('latitude', row.get('latitude', 0), 0),
                    ('longitude', row.get('longitude', 0), 0),
                    ('total_area', row.get('total_area', 0), 0),
                    ('number_of_rooms', row.get('number_of_rooms', 0), 0),
                    ('floor', row.get('floor', 0), 0),
                    ('total_floors', row.get('total_floors', 0), 0),
                    ('price_per_sqm', row.get('price_per_sqm', 0), 0),
                    ('price', row.get('price', 0), 0),
                    ('id', row.get('id', 0), 0),
                    ('last_refresh_time', row.get('last_refresh_time', 0), 0),
                    ('layout_name', row.get('layout_name', 'Unknown'), 'Unknown'),
                    ('foundation_name', row.get('foundation_name', 'Unknown'), 'Unknown'),
                    ('wc_name', row.get('wc_name', 'Unknown'), 'Unknown'),
                    ('repair_name', row.get('repair_name', 'Unknown'), 'Unknown'),
                    ('type_of_market_key', row.get('type_of_market_key', 'Unknown'), 'Unknown'),
                    ('is_furnished', row.get('is_furnished', 'Unknown'), 'Unknown'),
                    ('year_of_construction', row.get('year_of_construction', 0), 0),
                ]}
                # self.stdout.write(self.style.SUCCESS(row))

                city_dim = await sync_to_async(CityDim.objects.using('default').get_or_create)(
                    city_name=row['city_name'])
                region_dim = await sync_to_async(RegionDim.objects.using('default').get_or_create)(
                    region_name=mapping_dict_regions.get(row['region_name'], row['region_name'])
                )
                district_dim = await sync_to_async(DistrictDim.objects.using('default').get_or_create)(
                    district_name=mapping_dict_district.get(row['district_name'], row['district_name'])
                )
                lat_lon_dim = await sync_to_async(LatLonDim.objects.using('default').get_or_create)(
                    latitude=row['latitude'], longitude=row['longitude']
                )

                location, created_location = await sync_to_async(DimLocation.objects.using('default').get_or_create)(
                    city=city_dim[0],
                    region=region_dim[0],
                    district=district_dim[0],
                    lat_lon=lat_lon_dim[0]
                )
                row['number_of_rooms'] = clean_numbers(row.get('number_of_rooms'))
                row['total_area'] = clean_numbers(row.get('total_area'))
                row['floor'] = clean_numbers(row.get('floor'))
                row['total_floors'] = clean_numbers(row.get('total_floors'))
                row['price_per_sqm'] = clean_numbers(row.get('price_per_sqm'))
                row['price'] = clean_numbers(row.get('price'))

                numeric, created_numeric = await sync_to_async(DimNumeric.objects.using('default').get_or_create)(
                    total_area=row['total_area'],
                    number_of_rooms=row['number_of_rooms'],
                    floors=row['floor'],
                    total_floors=row['total_floors'],
                    price_per_sqm=row['price_per_sqm'],
                    price=row['price']
                )

                layout_dim = await sync_to_async(LayoutDim.objects.using('default').get_or_create)(
                    layout_name=row['layout_name']
                )
                foundation_dim = await sync_to_async(FoundationDim.objects.using('default').get_or_create)(
                    foundation_name=mapping_dict_foundation.get(row['foundation_name'], row['foundation_name'])
                )
                wc_dim = await sync_to_async(WCDim.objects.using('default').get_or_create)(
                    wc_name=row['wc_name']
                )
                repair_dim = await sync_to_async(RepairDim.objects.using('default').get_or_create)(
                    repair_name=row['repair_name']
                )

                characteristic, created_characteristic = await sync_to_async(
                    DimCharacteristic.objects.using('default').get_or_create)(
                    type_of_market=row['type_of_market_key'],
                    is_furnished=row['is_furnished'],
                    year_of_construction=row['year_of_construction'],
                    layout=layout_dim[0],
                    foundation=foundation_dim[0],
                    wc=wc_dim[0],
                    repair=repair_dim[0]
                )

                time_dim, created_time = await sync_to_async(DimTime.objects.using('default').get_or_create)(
                    datetime=add_timezone(row['last_refresh_time']),
                    defaults={
                        'year': add_timezone(row['last_refresh_time']).year,
                        'month': add_timezone(row['last_refresh_time']).month,
                        'day': add_timezone(row['last_refresh_time']).day,
                        'week': add_timezone(row['last_refresh_time']).isocalendar()[1],
                        'weekday': add_timezone(row['last_refresh_time']).strftime('%A')
                    }
                )

                await sync_to_async(FactApartments.objects.using('default').update_or_create)(
                    apartment_id=row['id'],
                    defaults={
                        'time': time_dim,
                        'location': location,
                        'numeric': numeric,
                        'characteristic': characteristic
                    }
                )
                if row['id'].startswith('O'):
                    loaded_counts['OLX'] += 1
                elif row['id'].startswith('U'):
                    loaded_counts['Uybor'] += 1
                elif row['id'].startswith('F'):
                    loaded_counts['FlatFile'] += 1
                etl_log.loaded_data = loaded_counts
                await sync_to_async(etl_log.save)()

                # self.stdout.write(self.style.SUCCESS(f"✅ Record {index + 1} processed successfully."))

            self.stdout.write(self.style.SUCCESS("✅ Data successfully inserted into SQLite3!"))
            # loaded_counts['OLX'] = olx_loaded_count
            # loaded_counts['Uybor'] = olx_loaded_count
            # loaded_counts['Flat'] = olx_loaded_count
            # etl_log.loaded_data = loaded_counts
            # etl_log.total_loaded = sum(loaded_counts.values())
            etl_log.status = "Success"
            await sync_to_async(etl_log.save)()
            await sync_to_async(etl_log.complete_etl)()

        except Exception as ex:
            self.stdout.write(self.style.ERROR(f"❌ Error processing data: {ex}"))
            etl_log.status = "Failed"
            etl_log.error_message = str(ex)
            await sync_to_async(etl_log.complete_etl)()
            pass
        finally:
            self.stdout.write(self.style.SUCCESS("✅ COMPLETED"))
