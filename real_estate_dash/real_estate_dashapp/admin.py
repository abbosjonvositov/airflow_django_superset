from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import CSVUpload, ETLLog
from django.contrib import admin
from django.utils.html import format_html
import os

@admin.register(CSVUpload)
class CSVUploadAdmin(admin.ModelAdmin):
    list_display = ("file", "uploaded_at", "delete_file_link")
    readonly_fields = ("uploaded_at",)

    def delete_model(self, request, obj):
        """Ensure file is deleted when instance is deleted."""
        if obj.file and os.path.isfile(obj.file.path):
            os.remove(obj.file.path)  # Delete the file from media folder
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """Ensure files are deleted when bulk deleting instances."""
        for obj in queryset:
            if obj.file and os.path.isfile(obj.file.path):
                os.remove(obj.file.path)
        queryset.delete()

    def delete_file_link(self, obj):
        """Display a delete file link in the admin panel (optional)."""
        if obj.file:
            return format_html('<a href="{}" style="color:red;" target="_blank">Delete File</a>', obj.file.url)
        return "-"
    delete_file_link.short_description = "Delete File"


from collections import defaultdict
from datetime import timedelta
from django.utils.timezone import now
from django.contrib import admin
from .models import ETLLog
import json

class ETLLogAdmin(admin.ModelAdmin):
    list_display = ("start_time", "end_time", "duration_seconds", "status")

    def changelist_view(self, request, extra_context=None):
        # Filter logs from the last 7 days
        last_7_days = now() - timedelta(days=7)
        etl_logs = ETLLog.objects.filter(start_time__gte=last_7_days)

        # Group by day and by source for extracted and loaded data
        daily_summary = defaultdict(lambda: {
            "Extracted Sources": defaultdict(int),
            "Loaded Sources": defaultdict(int),
        })
        for log in etl_logs:
            day = log.start_time.date()

            # Add breakdown for extracted data
            for source, count in log.extracted_data.items():
                daily_summary[day]["Extracted Sources"][source] += count

            # Add breakdown for loaded data
            for source, count in log.loaded_data.items():
                daily_summary[day]["Loaded Sources"][source] += count

        # Format the data for the chart
        etl_summary = {
            "Days": list(map(str, daily_summary.keys())),  # Dates as strings
            "Extracted Source Breakdown": {str(day): data["Extracted Sources"] for day, data in daily_summary.items()},
            "Loaded Source Breakdown": {str(day): data["Loaded Sources"] for day, data in daily_summary.items()},
        }

        extra_context = extra_context or {}
        extra_context["etl_summary"] = json.dumps(etl_summary)

        return super().changelist_view(request, extra_context=extra_context)

# Register the model with the admin site
admin.site.register(ETLLog, ETLLogAdmin)


