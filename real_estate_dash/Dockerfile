FROM python:3.13-slim-bullseye

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY ./req.txt .
RUN pip install --no-cache-dir -r req.txt

COPY . .

EXPOSE 8000

COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
