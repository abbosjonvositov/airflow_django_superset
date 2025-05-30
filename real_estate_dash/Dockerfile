# Use the official slim Python image
FROM python:3.13-slim-bullseye

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

# Add a startup script to handle conditional migrations
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set default entrypoint
ENTRYPOINT ["/entrypoint.sh"]
