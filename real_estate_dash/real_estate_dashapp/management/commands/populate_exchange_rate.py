import os
import pandas as pd
from django.core.management.base import BaseCommand
from real_estate_dashapp.models import ExchangeRateDim
from django.utils.dateparse import parse_datetime
from datetime import datetime
from django.conf import settings


class Command(BaseCommand):
    help = 'Populate exchange rate data from Excel files'

    def handle(self, *args, **kwargs):
        root_path = settings.BASE_DIR
        path_ = os.path.join(root_path, 'exchange_rate')
        if not os.path.exists(path_):
            self.stdout.write(self.style.ERROR(f"Directory not found: {path_}"))
            return

        file_count = 0
        record_count = 0
        for file in os.listdir(path_):
            if file.endswith(".xlsx") or file.endswith(".xls"):
                file_path = os.path.join(path_, file)
                df = pd.read_excel(file_path, skiprows=1)

                for item in df.itertuples():
                    date_ = item[1]
                    rate = item[3]

                    if pd.isna(date_) or pd.isna(rate):
                        continue

                    if isinstance(date_, datetime):
                        date_obj = date_
                    else:
                        try:
                            date_obj = pd.to_datetime(date_)
                        except Exception:
                            continue

                    try:
                        obj, created = ExchangeRateDim.objects.get_or_create(
                            datetime=date_obj,
                            defaults={'usd_uzs_rate': rate}
                        )
                        if not created:
                            obj.usd_uzs_rate = rate
                            obj.save()
                        record_count += 1
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Error processing row {item}: {e}"))

                file_count += 1

        self.stdout.write(self.style.SUCCESS(f"Processed {file_count} file(s), {record_count} records added/updated."))
