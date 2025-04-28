from django.urls import path
from .views import *

urlpatterns = [
    path('', BaseView.as_view(), name='base_view'),
    path('superset_dash', SuperSetView.as_view(), name='superset_view'),
    path('api/apartment-stats/', ApartmentStatsView.as_view(), name='apartment-stats'),
    path('api/listings-count-by-region/', ListingsCountByRegionView.as_view(), name='listings-count-by-region'),
    path('api/by-region-stats/', ByRegionOrDistrictStatsView.as_view(), name='by-region-stats'),
    path('api/by-listing-count-shares/', ListingsShareView.as_view(), name='by-term-region-stats'),
    path('api/monthly-average-price/', MonthlyAveragePriceAPIView.as_view(), name='avg-price-by-month'),
    path('get-geojson/', tashkent_geojson, name='get_geojson'),
    path("api/districts-count/", DistrictsCountView.as_view(), name="districts-count"),

]
