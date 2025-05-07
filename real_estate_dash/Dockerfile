# Use the official slim Python image
FROM python:3.13-slim-bullseye

USER root


# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY ./req.txt .
RUN pip install --no-cache-dir -r req.txt

# Copy Django project files
COPY . .

# Expose the default Django port
EXPOSE 8000

# Default command
CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
