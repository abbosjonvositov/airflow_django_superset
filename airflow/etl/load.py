import sys
import os

# Set Django project path
sys.path.append("/opt/airflow/django_project")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "real_estate_dash.settings")

import django

django.setup()

from real_estate_dashapp.models import DimTime  # Replace with actual model


def load_data():
    print("Loading data using Django ORM...")
