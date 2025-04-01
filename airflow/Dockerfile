FROM apache/airflow:latest

# Install Django and PostgreSQL dependencies using Airflow's recommended approach
USER airflow
COPY ./req.txt .
RUN pip install --no-cache-dir -r req.txt
