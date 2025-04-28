FROM apache/airflow:2.10.5

# Install Django and PostgreSQL dependencies using Airflow's recommended approach
USER airflow
COPY ./req.txt .
RUN pip install --no-cache-dir -r req.txt
