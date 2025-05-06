import sys
import os
from real_estate_dashapp.models import FactApartments, ExchangeRateDim
from django.utils.timezone import now, make_aware, is_naive
from datetime import datetime
import pandas as pd
import pytz
import json

# Set Django project path and settings
sys.path.append("/opt/airflow/django_project")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "real_estate_dash.settings")


def add_timezone(dt):
    if isinstance(dt, str):
        dt = datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%fZ')

    # Set dt as UTC first
    dt = dt.replace(tzinfo=pytz.utc)

    # Convert to Asia/Tashkent
    tashkent_tz = pytz.timezone('Asia/Tashkent')
    return dt.astimezone(tashkent_tz)


def extract_data_for_ml_algorithm(**context):

    districts = [
        'Чиланзарский район', 'Юнусабадский район', 'Янгихаётский район',
        'Яккасарайский район', 'Шайхантахурский район',
        'Мирабадский район', 'Учтепинский район', 'Яшнабадский район',
        'Бектемирский район', 'Сергелийский район',
        'Мирзо-Улугбекский район', 'Алмазарский район', 'Новый Ташкентский район'
    ]

    qs = FactApartments.objects.select_related(
        'location__city',
        'location__region',
        'location__district',
        'time',
        'characteristic',
        'characteristic__foundation',
        'characteristic__layout',
        'characteristic__repair',
        'characteristic__wc',
        'numeric'
    ).filter(
        location__district__district_name__in=districts,
        numeric__number_of_rooms__lte=7,
        numeric__total_floors__lte=16
    )[:100000]

    records = []

    for obj in qs:
        datetime_val = obj.time.datetime if obj.time and obj.time.datetime else None

        if datetime_val:
            if is_naive(datetime_val):
                aware_datetime = add_timezone(datetime_val)
            else:
                aware_datetime = datetime_val

            exchange = ExchangeRateDim.objects.filter(datetime__date=aware_datetime.date()).first()
            if not exchange:
                exchange = ExchangeRateDim.objects.filter(datetime__lt=aware_datetime).order_by('-datetime').first()
            exchange_rate = exchange.usd_uzs_rate if exchange else None
        else:
            aware_datetime = None
            exchange_rate = None

        price_uzs = obj.numeric.price if obj.numeric.price else None
        price_usd = price_uzs / exchange_rate if price_uzs and exchange_rate else None
        year_month = aware_datetime.strftime('%Y-%m') if aware_datetime else None

        records.append({
            'price_usd': price_usd,
            'year_month': year_month,
            'district_name': obj.location.district.district_name if obj.location and obj.location.district else None,
            'type_of_market': obj.characteristic.type_of_market if obj.characteristic else None,
            'foundation_name': obj.characteristic.foundation.foundation_name if obj.characteristic and obj.characteristic.foundation else None,
            'layout_name': obj.characteristic.layout.layout_name if obj.characteristic and obj.characteristic.layout else None,
            'repair_name': obj.characteristic.repair.repair_name if obj.characteristic and obj.characteristic.repair else None,
            'wc_name': obj.characteristic.wc.wc_name if obj.characteristic and obj.characteristic.wc else None,
            'total_area': obj.numeric.total_area if obj.numeric else None,
            'number_of_rooms': obj.numeric.number_of_rooms if obj.numeric else None,
            'floors': obj.numeric.floors if obj.numeric else None,
            'total_floors': obj.numeric.total_floors if obj.numeric else None,
        })

    df = pd.DataFrame(records)
    context['task_instance'].xcom_push(key='extract_data_for_analysis', value=df)
    # df.to_excel('test.xlsx', index=False)
    return '---EXTRACTED SUCCESSFULLY---'
