import sys
import os
import pymysql
import mysql.connector
import sshtunnel
import logging
from airflow.models import Variable
import time

# Configure logging for Airflow
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SSH_MySQL_Extractor")

# SSH Configuration
SSH_CONFIG = {
    "ssh_address": "ssh.pythonanywhere.com",
    "ssh_port": 22,
    "ssh_username": "gullolacorp",
    "ssh_password": Variable.get("SSH_PASSWORD"),
    "remote_bind_address": "gullolacorp.mysql.pythonanywhere-services.com",
    "remote_bind_port": 3306
}

# MySQL Configuration
MYSQL_CONFIG = {
    "user": "gullolacorp",
    "password": Variable.get("MYSQL_PASSWORD"),
    "db": "gullolacorp$default",
    "connect_timeout": 60
}

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


def ssh_tunnel_mysql_connection():
    """
    Establishes an SSH tunnel and connects to the MySQL database with retry logic.
    """
    attempts = 0

    while attempts < MAX_RETRIES:
        try:
            # Start SSH tunnel without timeout
            tunnel = sshtunnel.SSHTunnelForwarder(
                (SSH_CONFIG["ssh_address"], SSH_CONFIG["ssh_port"]),
                ssh_username=SSH_CONFIG["ssh_username"],
                ssh_password=SSH_CONFIG["ssh_password"],
                remote_bind_address=(SSH_CONFIG["remote_bind_address"], SSH_CONFIG["remote_bind_port"]),
            )
            tunnel.start()
            logger.info("🔗 SSH Tunnel established!")

            # Update MySQL host and port
            MYSQL_CONFIG["host"] = "127.0.0.1"
            MYSQL_CONFIG["port"] = tunnel.local_bind_port

            # Establish MySQL connection with timeout handling
            conn = mysql.connector.connect(
                host=MYSQL_CONFIG["host"],
                port=MYSQL_CONFIG["port"],
                user=MYSQL_CONFIG["user"],
                password=MYSQL_CONFIG["password"],
                database=MYSQL_CONFIG["db"],
                connect_timeout=MYSQL_CONFIG["connect_timeout"]
            )
            if conn.is_connected():
                logger.info("✅ Connected to MySQL database successfully!")
                return conn, tunnel  # Return both the connection and tunnel
            else:
                raise Exception("MySQL connection failed.")
        except Exception as e:
            attempts += 1
            logger.error(f"❌ Attempt {attempts} failed: {e}")
            if attempts < MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error("❌ Maximum retry attempts reached. Unable to establish connection.")
                raise e


def extract_data(source):
    """
    Extracts new records from the MySQL database for the given source (OLX or Uybor).
    """
    latest_timestamp = '2000-01-01'
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
            ORDER BY last_refresh_time ASC;
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
            ORDER BY updatedAt ASC;
        """
    }[source]

    try:
        db_conn, tunnel = ssh_tunnel_mysql_connection()  # Ensure connection before extraction
        if not db_conn or not tunnel:
            return None

        cursor = db_conn.cursor(dictionary=True)
        cursor.execute(query, (latest_timestamp,))
        data = cursor.fetchall()

        logger.info(f"✅ Fetched {len(data)} {source} records.")

        if not data:
            logger.warning(f"No data extracted for source: {source}")

        # Close MySQL connection and SSH tunnel
        cursor.close()
        db_conn.close()
        tunnel.stop()
        return data
    except Exception as e:
        logger.error(f"❌ Error extracting {source} data: {e}")
        raise
