#!/bin/bash

echo "Checking for pending migrations..."

# Check for unapplied migrations
UNAPPLIED_MIGRATIONS=$(python manage.py showmigrations --plan | grep '

\[ \]

' | wc -l)

if [ "$UNAPPLIED_MIGRATIONS" -gt 0 ]; then
    echo "Applying migrations..."
    python manage.py makemigrations
    python manage.py migrate --fake-initial
else
    echo "No migrations needed."
fi

# Start the Django server
exec python manage.py runserver 0.0.0.0:8000
