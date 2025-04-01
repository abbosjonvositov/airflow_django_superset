import sys
import os
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# Set Django project path
sys.path.append("/opt/airflow/django_project")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "real_estate_dash.settings")

import django

django.setup()

import sys
sys.path.append('/opt/airflow/etl')  # Manually add etl/ to Python path

from extract import extract_source_1, extract_source_2
from transform import transform_data
from load import load_data



default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 4, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'etl_dag',
    default_args=default_args,
    description='ETL Pipeline DAG',
    schedule_interval=timedelta(days=1),
)

extract_task_1 = PythonOperator(
    task_id='extract_source_1',
    python_callable=extract_source_1,
    dag=dag,
)

extract_task_2 = PythonOperator(
    task_id='extract_source_2',
    python_callable=extract_source_2,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_data_task',
    python_callable=load_data,
    dag=dag,
)

# Define Task Execution Order
extract_task_1 >> extract_task_2 >> transform_task >> load_task
