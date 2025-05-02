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

from extract import extract_data
from transform import transform_data
from load import load_data





default_args = {
    'owner': 'airflow',
    'depends_on_past': False,  # Prevents dependencies on previous task runs
    'start_date': datetime(2024, 4, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,  # Disable retries to avoid unintended task loops
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'etl_dag',
    default_args=default_args,
    description='ETL Pipeline DAG',
    schedule_interval=timedelta(days=1),  # Scheduled to run daily
    catchup=False,  # Disable catching up on missed runs
    max_active_runs=1,  # Limit DAG to one active instance
)

extract_task_olx = PythonOperator(
    task_id='extract_source_olx',
    python_callable=extract_data,
    op_kwargs={'source': 'OLX'},  # Pass arguments if needed
    dag=dag,
)

extract_task_uybor = PythonOperator(
    task_id='extract_source_uybor',
    python_callable=extract_data,
    op_kwargs={'source': 'Uybor'},  # Pass arguments if needed
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    provide_context=True,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_data_task',
    python_callable=load_data,
    provide_context=True,
    dag=dag,
)

# Define Task Execution Order
[extract_task_olx, extract_task_uybor] >> transform_task >> load_task
