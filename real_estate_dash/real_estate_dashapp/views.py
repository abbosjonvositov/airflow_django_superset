from logging import exception
from .forms import *
from django.db.models import Avg, Count, Q
from django.views.generic import TemplateView
from .models import *
from datetime import datetime, timedelta
from django.views import View
from collections import defaultdict
from django.utils.timezone import now
import numpy as np
import json
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .utils import rf_model_prediction
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.http import HttpResponse
from rest_framework.permissions import AllowAny  # Ensure public access
from django.http import JsonResponse
from rest_framework.views import APIView
from django.db.models import F
from django.contrib.auth.views import LoginView, LogoutView
import logging
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.signing import dumps, loads, BadSignature
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic.edit import FormView
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views import View
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.templatetags.static import static

logger = logging.getLogger(__name__)

tashkent_district_filter_map = {
    "Almazar": "Алмазарский район",
    "Bektemir": "Бектемирский район",
    "Mirabad": "Мирабадский район",
    "Mirzo Ulugbek": "Мирзо-Улугбекский район",
    "Sergeli": "Сергелийский район",
    "Uchtepa": "Учтепинский район",
    "Chilanzar": "Чиланзарский район",
    "Shaykhantokhur": "Шайхантахурский район",
    "Yunusabad": "Юнусабадский район",
    "Yakkasaray": "Яккасарайский район",
    "Yashnobod": "Яшнабадский район"
}


class BaseView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Example: Fetching unique values from FactApartments model
        context['option_number_of_rooms'] = [i for i in range(1, 10)]
        context['option_total_floors'] = [i for i in range(1, 17)]
        context['option_floors'] = [i for i in range(1, 17)]
        context['option_type_of_market'] = DimCharacteristic.objects.values_list('type_of_market', flat=True).distinct()
        context['option_foundation'] = FoundationDim.objects.values_list('foundation_name', flat=True).distinct()
        context['request'] = self.request

        return context


class SuperSetView(TemplateView):
    template_name = 'superset_dash.html'


class IndividualPredictionView(TemplateView):
    template_name = 'individual_prediction.html'

    def get_context_data(self, **kwargs):
        districts = [
            'Чиланзарский район', 'Юнусабадский район', 'Янгихаётский район',
            'Яккасарайский район', 'Шайхантахурский район',
            'Мирабадский район', 'Учтепинский район', 'Яшнабадский район',
            'Бектемирский район', 'Сергелийский район',
            'Мирзо-Улугбекский район', 'Алмазарский район', 'Новый Ташкентский район'
        ]
        layout_name = ['Раздельная', 'Смежно-раздельная', 'Смежная', 'Многоуровневая',
                       'Малосемейка', 'Студия', 'Пентхаус']
        foundation_name = ['Кирпичный', 'Панельный', 'Монолитный', 'Блочный', 'Деревянный']
        wc_name = ['Совмещенный', 'Раздельный', '2 санузла и более']
        year_month = ['2024-11', '2024-12', '2025-01', '2025-02', '2025-03', '2025-04', '2025-05']
        repair_name = ['Авторский проект', 'Евроремонт', 'Черновая отделка',
                       'Требует ремонта', 'Предчистовая отделка', 'Средний']
        type_of_market = {
            'yes': 1,
            'no': 0
        }

        context = super().get_context_data(**kwargs)
        context['districts'] = districts
        context['number_of_rooms'] = [i for i in range(1, 8)]
        context['floors'] = [i for i in range(1, 17)]
        context['total_floors'] = [i for i in range(1, 17)]
        context['foundation_name'] = foundation_name
        context['layout_name'] = layout_name
        context['wc_name'] = wc_name
        context['year_month'] = year_month
        context['repair_name'] = repair_name
        context['type_of_market'] = type_of_market

        return context


class IndividualPredictionAPI(APIView):
    def post(self, request):
        """Receives form data and caches it for later model predictions."""
        year, month = request.data.get('year_month').split('-')
        data = {
            'district_name': request.data.get('district_name'),
            'number_of_rooms': request.data.get('number_of_rooms'),
            'floors': request.data.get('floors'),
            'total_floors': request.data.get('total_floors'),
            'total_area': request.data.get('total_area'),
            'foundation_name': request.data.get('foundation_name'),
            'layout_name': request.data.get('layout_name'),
            'wc_name': request.data.get('wc_name'),
            'repair_name': request.data.get('repair_name'),
            'year': int(year),
            'month': int(month),
            'is_primary': request.data.get('is_primary')
        }
        # Cache data with a timeout (e.g., 5 minutes)
        cache.set('prediction_features', data, timeout=None)
        with open('response.json', 'w', encoding='utf-8-sig') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        return Response({"success": True, "message": "Features cached successfully."}, status=status.HTTP_200_OK)

    def get(self, request):
        """Retrieves cached features, applies the model, and returns the prediction."""

        data = cache.get('prediction_features')
        if not data:
            return Response({"success": False, "message": "No cached data found."}, status=status.HTTP_404_NOT_FOUND)

        # Apply model prediction using cached data
        results = rf_model_prediction([data])

        response_data = {
            'success': True,
            'data': data,
            'prediction': float(round(results['prediction'], 2)),
            'upper_bound': results['upper_bound'],
            'lower_bound': results['lower_bound'],
            'std_dev': results['std_dev'],
            'histogram': results['histogram']
        }

        return Response(response_data, status=status.HTTP_200_OK)


class BulkPredictionView(TemplateView):
    template_name = 'bulk_prediction.html'

    def get_context_data(self, **kwargs):
        districts = [
            'Чиланзарский район', 'Юнусабадский район', 'Янгихаётский район',
            'Яккасарайский район', 'Шайхантахурский район',
            'Мирабадский район', 'Учтепинский район', 'Яшнабадский район',
            'Бектемирский район', 'Сергелийский район',
            'Мирзо-Улугбекский район', 'Алмазарский район', 'Новый Ташкентский район'
        ]
        layout_name = ['Раздельная', 'Смежно-раздельная', 'Смежная', 'Многоуровневая',
                       'Малосемейка', 'Студия', 'Пентхаус']
        foundation_name = ['Кирпичный', 'Панельный', 'Монолитный', 'Блочный', 'Деревянный']
        wc_name = ['Совмещенный', 'Раздельный', '2 санузла и более']
        year_month = ['2024-11', '2024-12', '2025-01', '2025-02', '2025-03', '2025-04', '2025-05']
        repair_name = ['Авторский проект', 'Евроремонт', 'Черновая отделка',
                       'Требует ремонта', 'Предчистовая отделка', 'Средний']
        type_of_market = {
            'yes': 1,
            'no': 0
        }

        context = super().get_context_data(**kwargs)
        context['districts'] = districts
        context['number_of_rooms'] = [i for i in range(1, 8)]
        context['floors'] = [i for i in range(1, 17)]
        context['total_floors'] = [i for i in range(1, 17)]
        context['foundation_name'] = foundation_name
        context['layout_name'] = layout_name
        context['wc_name'] = wc_name
        context['year_month'] = year_month
        context['repair_name'] = repair_name
        context['type_of_market'] = type_of_market

        return context


class MLUIView(TemplateView):
    template_name = 'ml_ui.html'


class ApartmentStatsView(APIView):
    def get(self, request):
        # Get the latest 30 dates correctly
        latest_entries = FactApartments.objects.select_related("time").order_by("-time__datetime")
        latest_30_entries = latest_entries[:30]

        # Fix: Use last() on the full queryset before slicing
        default_from_date = latest_entries.last().time.datetime if latest_entries.exists() else None
        default_to_date = latest_30_entries.first().time.datetime if latest_30_entries.exists() else None

        # Get filter parameters
        num_rooms = request.GET.get("number_of_rooms")
        total_floors = request.GET.get("total_floors")
        floors = request.GET.get("floors")
        type_of_market = request.GET.get("type_of_market")
        region = request.GET.get("region")
        district = tashkent_district_filter_map.get(request.GET.get("district"), '')
        from_date = request.GET.get("from_date")
        to_date = request.GET.get("to_date")
        print(district)
        # Ensure the dates are in the correct format and use default values if empty
        try:
            if from_date:
                from_date = datetime.strptime(from_date, "%Y-%m-%d")
            else:
                from_date = default_from_date

            if to_date:
                to_date = datetime.strptime(to_date, "%Y-%m-%d")
            else:
                to_date = default_to_date
        except ValueError:
            # Handle invalid date format
            return Response({"error": "Invalid date format. Use 'YYYY-MM-DD'."}, status=400)

        # Base Queryset (filter by given date range or default to the latest 30 days)
        queryset = FactApartments.objects.select_related("numeric", "time", "location", "characteristic").filter(
            time__datetime__range=[from_date, to_date]
        )

        # Apply optional filters
        if num_rooms:
            queryset = queryset.filter(numeric__number_of_rooms=num_rooms)
        if total_floors:
            queryset = queryset.filter(numeric__total_floors=total_floors)
        if floors:
            queryset = queryset.filter(numeric__floors=floors)
        if type_of_market:
            queryset = queryset.filter(characteristic__type_of_market=type_of_market)
        if region:
            queryset = queryset.filter(location__region__region_name=region)
        if district:
            queryset = queryset.filter(location__district__district_name=district)

        # Aggregate calculations
        avg_price = queryset.aggregate(Avg("numeric__price"))["numeric__price__avg"]
        avg_price_sqm = queryset.aggregate(Avg("numeric__price_per_sqm"))["numeric__price_per_sqm__avg"]

        data = {
            "price_per_sqm": avg_price_sqm / 1000000 if avg_price_sqm else None,
            "avg_price": avg_price / 1000000 if avg_price else None,
            "price_per_sqm_usd": (avg_price_sqm / 13000) / 1000 if avg_price_sqm else None,
            "avg_price_usd": (avg_price / 13000) / 1000 if avg_price else None,
            "default_filters": {
                "from_date": default_from_date.strftime("%Y-%m-%d") if default_from_date else None,
                "to_date": default_to_date.strftime("%Y-%m-%d") if default_to_date else None,
            },
        }

        return Response(data)


class ByRegionOrDistrictStatsView(APIView):
    def get(self, request):
        # Get the latest 30 dates correctly
        latest_entries = FactApartments.objects.select_related("time").order_by("-time__datetime")
        latest_30_entries = latest_entries[:30]

        # Fix: Use last() on the full queryset before slicing
        default_from_date = latest_entries.last().time.datetime if latest_entries.exists() else None
        default_to_date = latest_30_entries.first().time.datetime if latest_30_entries.exists() else None

        # Get filter parameters
        num_rooms = request.GET.get("number_of_rooms")
        total_floors = request.GET.get("total_floors")
        floors = request.GET.get("floors")
        type_of_market = request.GET.get("type_of_market")
        region = request.GET.get("region")
        from_date = request.GET.get("from_date")
        to_date = request.GET.get("to_date")
        data_type = request.GET.get("data_type", "region").lower()  # Default to "region" if not provided

        # Ensure the dates are in the correct format and use default values if empty
        try:
            if from_date:
                from_date = datetime.strptime(from_date, "%Y-%m-%d")
            else:
                from_date = default_from_date

            if to_date:
                to_date = datetime.strptime(to_date, "%Y-%m-%d")
            else:
                to_date = default_to_date
        except ValueError:
            # Handle invalid date format
            return Response({"error": "Invalid date format. Use 'YYYY-MM-DD'."}, status=400)

        # Base Queryset (filter by given date range or default to the latest 30 days)
        queryset = FactApartments.objects.select_related("numeric", "time", "location", "characteristic").filter(
            time__datetime__range=[from_date, to_date]
        )

        # Apply optional filters
        if num_rooms:
            queryset = queryset.filter(numeric__number_of_rooms=num_rooms)
        if total_floors:
            queryset = queryset.filter(numeric__total_floors=total_floors)
        if floors:
            queryset = queryset.filter(numeric__floors=floors)
        if type_of_market:
            queryset = queryset.filter(characteristic__type_of_market=type_of_market)
        if region:
            queryset = queryset.filter(location__region__region_name=region)

        # Convert queryset to list for IQR filtering
        price_data = list(queryset.values_list("numeric__price", flat=True))
        price_data = [p for p in price_data if p is not None]

        if price_data:
            q1 = np.percentile(price_data, 25)
            q3 = np.percentile(price_data, 75)
            iqr = q3 - q1
            lower_bound = q1 - (1.5 * iqr)
            upper_bound = q3 + (1.5 * iqr)

            # Filter out outliers
            queryset = queryset.filter(Q(numeric__price__gte=lower_bound) & Q(numeric__price__lte=upper_bound))

        # Decide grouping based on data_type (default to "region")
        if data_type == "district":
            allowed_districts = [
                "Мирабадский район", "Яккасарайский район", "Мирзо-Улугбекский район",
                "Юнусабадский район", "Яшнабадский район", "Сергелийский район",
                "Учтепинский район", "Шайхантахурский район", "Чиланзарский район",
                "Алмазарский район", "Бектемирский район"
            ]
            grouped_data = queryset.values('location__district__district_name').annotate(
                avg_price=Avg('numeric__price'),
                avg_price_sqm=Avg('numeric__price_per_sqm')
            ).order_by('-avg_price')
            allowed_entities = allowed_districts
            entity_field = 'location__district__district_name'
        else:
            allowed_regions = [
                "andizhanskaya-oblast", "buharskaya-oblast", "dzhizakskaya-oblast",
                "ferganskaya-oblast", "horezmskaya-oblast", "karakalpakstan",
                "kashkadarinskaya-oblast", "namanganskaya-oblast", "navoijskaya-oblast",
                "samarkandskaya-oblast", "surhandarinskaya-oblast", "syrdarinskaya-oblast",
                "toshkent-oblast"
            ]
            grouped_data = queryset.values('location__region__region_name').annotate(
                avg_price=Avg('numeric__price'),
                avg_price_sqm=Avg('numeric__price_per_sqm')
            ).order_by('-avg_price')
            allowed_entities = allowed_regions
            entity_field = 'location__region__region_name'

        # Prepare response data
        data = defaultdict(dict)
        for entry in grouped_data:
            entity_name = entry.get(entity_field)
            if entity_name in allowed_entities:
                avg_price = entry['avg_price']
                data[entity_name] = {
                    "avg_price": round(avg_price / 1000000, 2) if avg_price else None,
                    "avg_price_usd": round((avg_price / 13000) / 1000, 2) if avg_price else None,
                }

        return Response(data)


class ListingsCountByRegionView(APIView):
    def get(self, request, *args, **kwargs):
        # Get filter parameters
        num_rooms = request.GET.get("number_of_rooms")
        total_floors = request.GET.get("total_floors")
        floors = request.GET.get("floors")
        type_of_market = request.GET.get("type_of_market")
        region = request.GET.get("region")

        # Base Queryset
        queryset = FactApartments.objects.select_related("numeric", "location", "characteristic")

        # Apply optional filters
        if num_rooms:
            queryset = queryset.filter(numeric__number_of_rooms=num_rooms)
        if total_floors:
            queryset = queryset.filter(numeric__total_floors=total_floors)
        if floors:
            queryset = queryset.filter(numeric__floors=floors)
        if type_of_market:
            queryset = queryset.filter(characteristic__type_of_market=type_of_market)
        if region:
            queryset = queryset.filter(location__region__region_name=region)

        # Count listings per region
        listings_count = queryset.values('location__region__region_name').annotate(count=models.Count('id'))

        # Prepare response data
        response_data = {
            region['location__region__region_name']: region['count']
            for region in listings_count if region['count'] > 1
        }

        return Response(response_data)


class ListingsShareView(View):
    def get(self, request, *args, **kwargs):
        allowed_regions = [
            "andizhanskaya-oblast", "buharskaya-oblast", "dzhizakskaya-oblast",
            "ferganskaya-oblast", "horezmskaya-oblast", "karakalpakstan",
            "kashkadarinskaya-oblast", "namanganskaya-oblast", "navoijskaya-oblast",
            "samarkandskaya-oblast", "surhandarinskaya-oblast", "syrdarinskaya-oblast",
            "toshkent-oblast"
        ]

        listings_count = (
            FactApartments.objects
            .values('location__region__region_name')
            .annotate(count=models.Count('id'))
        )

        total_listings = sum(region['count'] for region in listings_count)

        response_data = {
            region['location__region__region_name']: round((region['count'] / total_listings) * 100, 2)
            for region in listings_count
            if total_listings > 0 and region['location__region__region_name'] in allowed_regions
        }

        return JsonResponse(response_data)


class MonthlyAveragePriceAPIView(APIView):
    def get(self, request):
        allowed_regions = [
            "andizhanskaya-oblast", "buharskaya-oblast", "dzhizakskaya-oblast",
            "ferganskaya-oblast", "horezmskaya-oblast", "karakalpakstan",
            "kashkadarinskaya-oblast", "namanganskaya-oblast", "navoijskaya-oblast",
            "samarkandskaya-oblast", "surhandarinskaya-oblast", "syrdarinskaya-oblast",
            "toshkent-oblast"
        ]
        allowed_districts = [
            "Мирабадский район", "Яккасарайский район", "Мирзо-Улугбекский район",
            "Юнусабадский район", "Яшнабадский район", "Сергелийский район",
            "Учтепинский район", "Шайхантахурский район", "Чиланзарский район",
            "Алмазарский район", "Бектемирский район"
        ]

        # Get the latest available date
        latest_time = DimTime.objects.order_by('-year', '-month').first()
        if not latest_time:
            return Response({"error": "No data available"}, status=404)

        latest_year = latest_time.year
        latest_month = latest_time.month

        # Get the last 6 months dynamically
        months_data = []
        for i in range(6):
            year, month = latest_year, latest_month - i
            if month <= 0:  # Handle year transition
                year -= 1
                month += 12
            months_data.append((year, month))

        # Reverse to ensure latest appears first
        months_data.reverse()

        # Get filter parameters
        num_rooms = request.GET.get("number_of_rooms")
        total_floors = request.GET.get("total_floors")
        floors = request.GET.get("floors")
        type_of_market = request.GET.get("type_of_market")
        region = request.GET.get("region")
        data_type = request.GET.get("data_type", "region").lower()
        district = request.GET.get("district")

        # Fetch data and compute average price per region with IQR filtering
        response_data = {}
        if data_type == 'district':
            for district_obj in DistrictDim.objects.all():
                district_name = district_obj.district_name
                if region and district_name != region:
                    continue

                data = []
                for year, month in months_data:
                    queryset = FactApartments.objects.filter(
                        time__year=year, time__month=month, location__district=district_obj
                    )

                    # Apply optional filters
                    if num_rooms:
                        queryset = queryset.filter(numeric__number_of_rooms=num_rooms)
                    if total_floors:
                        queryset = queryset.filter(numeric__total_floors=total_floors)
                    if floors:
                        queryset = queryset.filter(numeric__floors=floors)
                    if type_of_market:
                        queryset = queryset.filter(characteristic__type_of_market=type_of_market)

                    # Get price values, filtering out None values
                    prices = [p for p in queryset.values_list('numeric__price', flat=True) if p is not None]

                    if prices:
                        # Compute IQR (Interquartile Range)
                        q1, q3 = np.percentile(prices, [25, 75])
                        iqr = q3 - q1
                        lower_bound = q1 - 1.5 * iqr
                        upper_bound = q3 + 1.5 * iqr

                        # Filter out both lower and upper outliers
                        filtered_prices = [p for p in prices if lower_bound <= p <= upper_bound]

                        avg_price = np.mean(filtered_prices) if filtered_prices else 0.0
                    else:
                        avg_price = 0.0

                    # Convert to "YYYY-MM" format
                    month_name = f"{year}-{month:02}"  # Ensures two-digit month
                    data.append([month_name, round(avg_price / 1_000_000, 2)])

                if district_name in allowed_districts:
                    response_data[district_name] = {
                        "district": district_name,
                        "data": data
                    }
        else:
            for region_obj in RegionDim.objects.all():
                region_name = region_obj.region_name
                if region and region_name != region:
                    continue

                data = []
                for year, month in months_data:
                    queryset = FactApartments.objects.filter(
                        time__year=year, time__month=month, location__region=region_obj
                    )

                    # Apply optional filters
                    if num_rooms:
                        queryset = queryset.filter(numeric__number_of_rooms=num_rooms)
                    if total_floors:
                        queryset = queryset.filter(numeric__total_floors=total_floors)
                    if floors:
                        queryset = queryset.filter(numeric__floors=floors)
                    if type_of_market:
                        queryset = queryset.filter(characteristic__type_of_market=type_of_market)

                    # Get price values, filtering out None values
                    prices = [p for p in queryset.values_list('numeric__price', flat=True) if p is not None]

                    if prices:
                        # Compute IQR (Interquartile Range)
                        q1, q3 = np.percentile(prices, [25, 75])
                        iqr = q3 - q1
                        lower_bound = q1 - 1.5 * iqr
                        upper_bound = q3 + 1.5 * iqr

                        # Filter out both lower and upper outliers
                        filtered_prices = [p for p in prices if lower_bound <= p <= upper_bound]

                        avg_price = np.mean(filtered_prices) if filtered_prices else 0.0
                    else:
                        avg_price = 0.0

                    # Convert to "YYYY-MM" format
                    month_name = f"{year}-{month:02}"  # Ensures two-digit month
                    data.append([month_name, round(avg_price / 1_000_000, 2)])

                if region_name in allowed_regions:
                    response_data[region_name] = {
                        "region": region_name,
                        "data": data
                    }

        return Response(response_data)


def tashkent_geojson(request):
    file_path = os.path.join(settings.BASE_DIR, 'real_estate_dashapp', 'static', 'tashkent_geo.json')
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return JsonResponse(data, safe=False)
    except FileNotFoundError:
        return JsonResponse({'error': 'File not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)


class DistrictsCountView(APIView):
    def get(self, request, *args, **kwargs):
        ALLOWED_DISTRICTS = [
            "Мирабадский район", "Яккасарайский район", "Мирзо-Улугбекский район",
            "Юнусабадский район", "Яшнабадский район", "Сергелийский район",
            "Учтепинский район", "Шайхантахурский район", "Чиланзарский район",
            "Алмазарский район", "Бектемирский район"
        ]
        # Get filter parameters
        num_rooms = request.GET.get("number_of_rooms")
        total_floors = request.GET.get("total_floors")
        floors = request.GET.get("floors")
        type_of_market = request.GET.get("type_of_market")
        region_name = request.GET.get("region_name")  # New filter for region

        # Base Queryset
        queryset = FactApartments.objects.select_related("numeric", "location", "characteristic")

        # Apply optional filters
        if num_rooms:
            queryset = queryset.filter(numeric__number_of_rooms=num_rooms)
        if total_floors:
            queryset = queryset.filter(numeric__total_floors=total_floors)
        if floors:
            queryset = queryset.filter(numeric__floors=floors)
        if type_of_market:
            queryset = queryset.filter(characteristic__type_of_market=type_of_market)
        if region_name:
            queryset = queryset.filter(location__region__region_name=region_name)

        # Count listings per district
        district_counts = (
            queryset.values("location__district__district_name")
            .annotate(count=models.Count("id"))
        )

        # Prepare response data
        response_data = {
            district["location__district__district_name"]: district["count"]
            for district in district_counts if district["location__district__district_name"] in ALLOWED_DISTRICTS
        }

        return Response(response_data)


class DownloadBulkTemplate(APIView):
    permission_classes = [AllowAny]  # Allow anyone to access

    def get(self, request, *args, **kwargs):
        # Define the template file path
        file_path = os.path.join(settings.BASE_DIR, "real_estate_dashapp/bulk_template/bulk_template.xlsx")

        # Check if the file exists
        if not os.path.exists(file_path):
            return HttpResponse("File not found", status=404)

        # Open the file and prepare response
        with open(file_path, "rb") as file:
            response = HttpResponse(file.read(),
                                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            response["Content-Disposition"] = 'attachment; filename="bulk_template.xlsx"'
            return response


class MetricsAPIView(APIView):
    def get(self, request):
        model_type = request.query_params.get('model_type', None)
        if not model_type:
            return Response({'error': 'model_type parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = Model.objects.filter(model_type__icontains=model_type).annotate(
            data_range_end=F('training_data__data_range_end'),
            r2=F('metrics__r2'),
            mape=F('metrics__mape'),
            rmse=F('metrics__rmse'),
            mse=F('metrics__mse'),
            mae=F('metrics__mae')
        ).values('data_range_end', 'r2', 'mape', 'rmse', 'mse', 'mae')

        metrics_dict = {}
        earliest_data_range = queryset.order_by('data_range_end').first()['data_range_end'].strftime('%Y-%m')
        for data in queryset:
            data_range = f"{earliest_data_range} {data['data_range_end'].strftime('%Y-%m')}"  # Adjusted format
            for metric in ['r2', 'mape', 'rmse', 'mse', 'mae']:
                if metric not in metrics_dict:
                    metrics_dict[metric] = {}
                metrics_dict[metric][data_range] = round(data[metric], 4)

        return Response(metrics_dict, status=status.HTTP_200_OK)


class UserLoginView(LoginView):
    template_name = "login.html"
    redirect_authenticated_user = True  # Redirect already logged-in users

    def get_success_url(self):
        return reverse_lazy("base_view")  # Correct way to redirect


class UserRegisterView(FormView):
    template_name = "signup.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("verify_email_notice")

    from django.templatetags.static import static

    def form_valid(self, form):
        data = form.cleaned_data
        token = dumps(data)

        verification_url = self.request.build_absolute_uri(
            reverse("verify_email", args=[token])
        )
        # banner_url = self.request.build_absolute_uri(static("vendors/images/black_banner.png"))

        context = {
            "username": data["username"],
            "verification_url": verification_url,
        }

        subject = "Activate Your Account"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = data["email"]

        text_body = render_to_string("emails/activation_email.txt", context)
        html_body = render_to_string("emails/activation_email.html", context)

        try:
            msg = EmailMultiAlternatives(subject, text_body, from_email, [to_email])
            msg.attach_alternative(html_body, "text/html")
            msg.send()
            logger.info(f"Verification email sent to {to_email}")
        except Exception as e:
            logger.exception("Error sending verification email")
            return render(self.request, "email_verification_failed.html", {"error": str(e)})

        return HttpResponseRedirect(self.get_success_url())


class VerifyEmailView(View):
    def get(self, request, token):
        try:
            data = loads(token)

            if User.objects.filter(username=data["username"]).exists():
                logger.warning("Duplicate registration attempt for username: %s", data["username"])
                return render(request, "email_verification_failed.html", {"error": "User already exists."})

            user = User.objects.create_user(
                username=data["username"],
                email=data["email"],
                password=data["password1"]
            )
            user.is_active = True
            user.save()

            login(request, user)
            logger.info("User verified and logged in: %s", user.username)
            return redirect("login")
        except (BadSignature, KeyError, Exception) as e:
            logger.exception("Email verification failed")
            return render(request, "email_verification_failed.html")


class ResendVerificationView(View):
    def get(self, request):
        if not request.user.is_authenticated or request.user.is_active:
            return redirect("login")

        data = {
            "username": request.user.username,
            "email": request.user.email,
            "password1": request.user.password,
        }

        token = dumps(data)
        verification_url = request.build_absolute_uri(
            reverse("verify_email", args=[token])
        )

        try:
            send_mail(
                subject="Verify your email",
                message=f"Here’s your verification link again:\n{verification_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[data["email"]],
            )
            logger.info(f"Resent verification email to {data['email']}")
        except Exception as e:
            logger.exception("Error resending verification email")
            return render(request, "email_verification_failed.html", {"error": str(e)})

        return redirect("verify_email_notice")


class UserLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("login")  # Replace with your desired redirect URL name
