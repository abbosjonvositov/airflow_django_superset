import sys
import os
import pymysql
import mysql.connector
import sshtunnel

from django.utils.timezone import now
from django.db.models import Max
from real_estate_dashapp.models import DimTime
from utils import XComDataWrapper

# Set Django project path and settings
sys.path.append("/opt/airflow/django_project")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "real_estate_dash.settings")

import django

django.setup()

# SSH Configuration
SSH_CONFIG = {
    "ssh_address": "ssh.pythonanywhere.com",
    "ssh_port": 22,
    "ssh_username": "gullolacorp",
    "ssh_password": "iambadguy571",
    "remote_bind_address": "gullolacorp.mysql.pythonanywhere-services.com",
    "remote_bind_port": 3306
}

# MySQL Configuration
MYSQL_CONFIG = {
    "user": "gullolacorp",
    "password": "iambadguy571",
    "db": "gullolacorp$default",
    "connect_timeout": 60
}


def ssh_tunnel_mysql_connection():
    """
    Establishes an SSH tunnel and connects to the MySQL database.
    """
    try:
        # Start SSH tunnel
        tunnel = sshtunnel.SSHTunnelForwarder(
            (SSH_CONFIG["ssh_address"], SSH_CONFIG["ssh_port"]),
            ssh_username=SSH_CONFIG["ssh_username"],
            ssh_password=SSH_CONFIG["ssh_password"],
            remote_bind_address=(SSH_CONFIG["remote_bind_address"], SSH_CONFIG["remote_bind_port"])
        )
        tunnel.start()
        print("🔗 SSH Tunnel established!")

        # Update MySQL host and port
        MYSQL_CONFIG["host"] = "127.0.0.1"
        MYSQL_CONFIG["port"] = tunnel.local_bind_port

        # Connect to MySQL database
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        if conn.is_connected():
            print("✅ Connected to MySQL database successfully!")
            return conn, tunnel  # Return both the connection and tunnel
        else:
            raise RuntimeError("❌ MySQL connection failed.")
    except Exception as e:
        raise RuntimeError(f"❌ Error establishing SSH tunnel or MySQL connection: {e}")


def fetch_latest_timestamp(source_prefix):
    """
    Fetches the latest timestamp for a given source (OLX or Uybor) using Django models.
    """
    try:
        latest_entry = DimTime.objects.filter(
            factapartments__apartment_id__startswith=source_prefix
        ).aggregate(Max('datetime'))
        latest_timestamp = latest_entry['datetime__max'] or now().replace(year=2000)
        print(f"📅 Latest {source_prefix} timestamp: {latest_timestamp}")
        return latest_timestamp
    except Exception as e:
        print(f"❌ Error fetching latest timestamp for {source_prefix}: {e}")
        return '2000-01-01'


def extract_data(source):
    """
    Extracts new records from the MySQL database for the given source (OLX or Uybor).
    """
    # Fetch latest timestamp or fallback to default

    latest_timestamp = fetch_latest_timestamp("O" if source == "OLX" else "U")
    if not latest_timestamp:
        latest_timestamp = '2000-01-01'

    # Query mapping
    query = {
        "OLX": """
            SELECT id, last_refresh_time, total_area_key AS total_area, number_of_rooms_key AS number_of_rooms,
                   floor_key AS floor, total_floors_key AS total_floors,
                   price / NULLIF(total_area_key, 0) AS price_per_sqm, price, type_of_market_key,
                   furnished_label AS is_furnished, year_of_construction_sale_key AS year_of_construction,
                   layout_label AS layout_name, house_type_label AS foundation_name, wc_label AS wc_name,
                   location_city_normalized_name AS city_name, location_district_name AS district_name,
                   map_lat AS latitude, map_lon AS longitude, repairs_label AS repair_name,
                   location_region_normalized_name AS region_name
            FROM olx_data
            WHERE last_refresh_time > %s
            ORDER BY last_refresh_time ASC
            LIMIT 100;
        """,
        "Uybor": """
            SELECT id, updatedAt AS last_refresh_time, square AS total_area, room AS number_of_rooms,
                   floor, floorTotal AS total_floors, priceEquivalent / NULLIF(square, 0) AS price_per_sqm,
                   priceEquivalent AS price,
                   CASE WHEN isNewBuilding = 'True' THEN 'primary' ELSE 'secondary' END AS type_of_market_key,
                   foundation AS foundation_name, region_name_ru AS region_name, district_name_ru AS district_name,
                   lat AS latitude, lng AS longitude, repair AS repair_name
            FROM uybor_data
            WHERE operationType = 'sale' AND updatedAt > %s
            ORDER BY updatedAt ASC
            LIMIT 100;
        """
    }[source]

    try:
        db_conn, tunnel = ssh_tunnel_mysql_connection()
        cursor = db_conn.cursor(dictionary=True)
        print(f"🔄 Fetching records for {source} starting from {latest_timestamp}")
        cursor.execute(query, (latest_timestamp,))
        data = cursor.fetchall()

        if not data:
            print(f"⚠️ No new records fetched for {source}. Task will skip further processing.")
            data = []  # Prevent failure, return empty list instead

        print(f"✅ Fetched {len(data)} {source} records.")

        # Close MySQL connection and SSH tunnel
        cursor.close()
        db_conn.close()
        tunnel.stop()
        return data
    except Exception as e:
        raise RuntimeError(f"❌ Error extracting {source} data: {e}")

# print(extract_data('OLX'))
