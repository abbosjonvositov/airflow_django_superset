from django.db import models
import os
from django.utils.timezone import now




class LayoutDim(models.Model):
    layout_name = models.CharField(max_length=255, unique=True, blank=True, null=True)

    class Meta:
        db_table = 'layout_dim'


class FoundationDim(models.Model):
    foundation_name = models.CharField(max_length=255, unique=True, blank=True, null=True)

    class Meta:
        db_table = 'foundation_dim'


class WCDim(models.Model):
    wc_name = models.CharField(max_length=255, unique=True, blank=True, null=True)

    class Meta:
        db_table = 'wc_dim'


class RepairDim(models.Model):
    repair_name = models.CharField(max_length=255, unique=True, blank=True, null=True)

    class Meta:
        db_table = 'repair_dim'


class DimCharacteristic(models.Model):
    type_of_market = models.CharField(max_length=255, blank=True, null=True)
    is_furnished = models.CharField(max_length=255, blank=True, null=True)
    year_of_construction = models.IntegerField(blank=True, null=True)
    layout = models.ForeignKey(LayoutDim, on_delete=models.CASCADE, blank=True, null=True)
    foundation = models.ForeignKey(FoundationDim, on_delete=models.CASCADE, blank=True, null=True)
    wc = models.ForeignKey(WCDim, on_delete=models.CASCADE, blank=True, null=True)
    repair = models.ForeignKey(RepairDim, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'dim_characteristic'


class CityDim(models.Model):
    city_name = models.CharField(max_length=255, unique=True, blank=True, null=True)

    class Meta:
        db_table = 'city_dim'


class RegionDim(models.Model):
    region_name = models.CharField(max_length=255, unique=True, blank=True, null=True)

    class Meta:
        db_table = 'region_dim'


class DistrictDim(models.Model):
    district_name = models.CharField(max_length=255, unique=True, blank=True, null=True)

    class Meta:
        db_table = 'district_dim'


class LatLonDim(models.Model):
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'lat_lon_dim'


class DimLocation(models.Model):
    city = models.ForeignKey(CityDim, on_delete=models.CASCADE, blank=True, null=True)
    region = models.ForeignKey(RegionDim, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(DistrictDim, on_delete=models.CASCADE, blank=True, null=True)
    lat_lon = models.ForeignKey(LatLonDim, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'dim_location'


class DimNumeric(models.Model):
    total_area = models.FloatField(blank=True, null=True)
    number_of_rooms = models.FloatField(blank=True, null=True)
    floors = models.FloatField(blank=True, null=True)
    total_floors = models.FloatField(blank=True, null=True)
    price_per_sqm = models.FloatField(blank=True, null=True)
    price = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'dim_numeric'


class DimTime(models.Model):
    datetime = models.DateTimeField(blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    month = models.IntegerField(blank=True, null=True)
    day = models.IntegerField(blank=True, null=True)
    week = models.IntegerField(blank=True, null=True)
    weekday = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'dim_time'


class FactApartments(models.Model):
    apartment_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    time = models.ForeignKey(DimTime, on_delete=models.CASCADE, blank=True, null=True)
    location = models.ForeignKey(DimLocation, on_delete=models.CASCADE, blank=True, null=True)
    numeric = models.ForeignKey(DimNumeric, on_delete=models.CASCADE, blank=True, null=True)
    characteristic = models.ForeignKey(DimCharacteristic, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'fact_apartments'


class ExchangeRateDim(models.Model):
    datetime = models.DateTimeField(unique=True)
    usd_uzs_rate = models.FloatField()

    class Meta:
        db_table = 'exchange_rate_dim'




def upload_csv_path(instance, filename):
    return filename  # Saves file directly to MEDIA_ROOT without additional directories


class CSVUpload(models.Model):
    file = models.FileField(upload_to=upload_csv_path)
    uploaded_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.file.name} - {self.uploaded_at}"


from django.db import models
from django.utils.timezone import now


class ETLLog(models.Model):
    start_time = models.DateTimeField(default=now)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)

    extracted_data = models.JSONField(default=dict)  # Stores { "OLX": 500, "Uybor": 300, ... }
    loaded_data = models.JSONField(default=dict)  # Stores { "OLX": 480, "Uybor": 290, ... }

    total_extracted = models.IntegerField(default=0)
    total_loaded = models.IntegerField(default=0)

    status = models.CharField(
        max_length=20,
        default="Start"
    )
    error_message = models.TextField(blank=True, null=True)

    def complete_etl(self):
        """ Updates end time and duration. """
        self.end_time = now()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        self.save()

    def __str__(self):
        return f"ETL Run - {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}"
