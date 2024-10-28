FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    cron \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

 #|-data_collection
 #| |-tests
 #| | |-test_data_collection.py
 #| | |-tracker.log
 #| | |-__pycache__
 #| | | |-test_data_collection.cpython-310-pytest-7.1.2.pyc
 #| | |-.pytest_cache
 #| | | |-CACHEDIR.TAG
 #| | | |-README.md
 #| | | |-.gitignore
 #| | | |-v
 #| | | | |-cache
 #| | | | | |-stepwise
 #| | | | | |-nodeids
 #| | | | | |-lastfailed
 #| |-src
 #| | |-data_collection.py
 #| | |-tracker.log
 #| | |-__pycache__
 #| | | |-data_collection.cpython-310.pyc
COPY data_collection/src/ /app/data_collection/src/
COPY docker/startup.sh /app/startup.sh

RUN mkdir -p /app/data

ENV DB_PATH=/app/data/exchange_rates.db

COPY docker/crontab /etc/cron.d/currency-updater
RUN chmod 0644 /etc/cron.d/currency-updater

RUN touch /var/log/cron.log
RUN chmod +x /app/startup.sh

CMD ["/app/startup.sh"]
