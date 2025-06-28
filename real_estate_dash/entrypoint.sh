#!/bin/bash

echo "Checking for pending migrations..."

# Check for unapplied migrations
UNAPPLIED_MIGRATIONS=$(python manage.py showmigrations --plan | grep '\[ \]' | wc -l)

if [ "$UNAPPLIED_MIGRATIONS" -gt 0 ]; then
    echo "Applying migrations..."
    python manage.py makemigrations
    python manage.py migrate --fake-initial
else
    echo "No migrations needed."
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn server..."
exec gunicorn real_estate_dash.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --log-level info
