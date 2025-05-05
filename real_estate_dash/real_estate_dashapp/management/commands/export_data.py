import logging
import pandas as pd
from django.utils.timezone import now, make_aware, is_naive
from django.core.management.base import BaseCommand
from real_estate_dashapp.models import FactApartments, ExchangeRateDim

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('apartment_export.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class Command(BaseCommand):
    help = 'Exports apartment data to XLSX using pandas with logging and proper timezone handling.'

    def handle(self, *args, **kwargs):
        logger.info("Starting export of apartment data")

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
        ).all()

        records = []

        for obj in qs:
            datetime_val = obj.time.datetime if obj.time and obj.time.datetime else None

            if datetime_val:
                if is_naive(datetime_val):
                    aware_datetime = make_aware(datetime_val)
                else:
                    aware_datetime = datetime_val

                # Get exchange rate for the date, fallback to previous if not available
                exchange = ExchangeRateDim.objects.filter(datetime__date=aware_datetime.date()).first()
                if not exchange:
                    exchange = ExchangeRateDim.objects.filter(datetime__lt=aware_datetime).order_by('-datetime').first()
                exchange_rate = exchange.usd_uzs_rate if exchange else None
            else:
                aware_datetime = None
                exchange_rate = None

            records.append({
                'apartment_id': obj.apartment_id,
                'city_name': obj.location.city.city_name if obj.location and obj.location.city else None,
                'region_name': obj.location.region.region_name if obj.location and obj.location.region else None,
                'district_name': obj.location.district.district_name if obj.location and obj.location.district else None,
                'datetime': aware_datetime.replace(tzinfo=None) if aware_datetime else None,  # Remove tzinfo
                'type_of_market': obj.characteristic.type_of_market if obj.characteristic else None,
                'foundation_name': obj.characteristic.foundation.foundation_name if obj.characteristic and obj.characteristic.foundation else None,
                'layout_name': obj.characteristic.layout.layout_name if obj.characteristic and obj.characteristic.layout else None,
                'repair_name': obj.characteristic.repair.repair_name if obj.characteristic and obj.characteristic.repair else None,
                'wc_name': obj.characteristic.wc.wc_name if obj.characteristic and obj.characteristic.wc else None,
                'total_area': obj.numeric.total_area if obj.numeric else None,
                'number_of_rooms': obj.numeric.number_of_rooms if obj.numeric else None,
                'floors': obj.numeric.floors if obj.numeric else None,
                'total_floors': obj.numeric.total_floors if obj.numeric else None,
                'price_per_sqm': obj.numeric.price_per_sqm if obj.numeric else None,
                'price': obj.numeric.price if obj.numeric else None,
                'usd_uzs_rate': exchange_rate
            })

        df = pd.DataFrame(records)

        timestamp = now().strftime('%Y%m%d_%H%M%S')
        filename = f"apartment_export_{timestamp}.xlsx"

        try:
            df.to_excel(filename, index=False)
            self.stdout.write(self.style.SUCCESS(f'Successfully exported to {filename}'))
            logger.info(f'Successfully exported to {filename}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to export: {e}'))
            logger.error(f'Export failed: {e}', exc_info=True)
