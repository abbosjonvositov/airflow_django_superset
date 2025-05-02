from rest_framework import serializers
from .models import FactApartments, DimNumeric


class FactApartmentsSerializer(serializers.ModelSerializer):
    price_per_sqm_usd = serializers.SerializerMethodField()
    avg_price_usd = serializers.SerializerMethodField()

    class Meta:
        model = FactApartments
        fields = ['numeric__price_per_sqm', 'numeric__price', 'price_per_sqm_usd', 'avg_price_usd']

    def get_price_per_sqm_usd(self, obj):
        return round(obj.numeric.price_per_sqm / 13000, 2) if obj.numeric.price_per_sqm else None

    def get_avg_price_usd(self, obj):
        return round(obj.numeric.price / 13000, 2) if obj.numeric.price else None
