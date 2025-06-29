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
import os

sys.path.append(os.path.abspath('/opt/airflow/ml_pipeline'))

from ml_pipeline_extract import extract_data_for_ml_algorithm
from ml_pipeline_data_preprocess import data_preprocess
from xgboost_algo import xgboost_algo

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
    'ml_pipeline_xgboost',
    default_args=default_args,
    description='ML Pipeline XGBoost',
    schedule_interval=timedelta(days=1),  # Scheduled to run daily
    catchup=False,  # Disable catching up on missed runs
    max_active_runs=1,  # Limit DAG to one active instance
)

extract_data_for_analysis = PythonOperator(
    task_id='extract_data_for_analysis',
    python_callable=extract_data_for_ml_algorithm,
    dag=dag,
)

preprocess_data_for_analysis = PythonOperator(
    task_id='preprocess_data_for_analysis',
    python_callable=data_preprocess,
    dag=dag,
)

# random_forrest_algorithm = PythonOperator(
#     task_id='random_forrest_algorithm_train',
#     python_callable=random_forest_algo,
#     dag=dag,
# )
#
xgboost_algorithm = PythonOperator(
    task_id='xgboost_algorithm_train',
    python_callable=xgboost_algo,
    dag=dag,
)

# lightgbm_algorithm = PythonOperator(
#     task_id='lightgbm_algorithm_train',
#     python_callable=lightgbm_algorithm,
#     dag=dag,
# )

# Define Task Execution Order
extract_data_for_analysis >> preprocess_data_for_analysis >> xgboost_algorithm
