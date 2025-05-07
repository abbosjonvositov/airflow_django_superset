FROM apache/airflow:2.10.5

# Switch to root to install system dependencies
USER root

# Install system packages
RUN apt-get update && apt-get install -y libgomp1

# Switch back to Airflow user for running Airflow processes
USER airflow

# Copy and install Python dependencies
COPY ./req.txt .
RUN pip install --no-cache-dir -r req.txt
