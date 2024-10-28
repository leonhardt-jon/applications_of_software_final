# docker/api.Dockerfile
FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy application code

 #|-data_analysis
 #| |-tests
 #| | |-test_analysis_server.py
 #| | |-tracker.log
 #| | |-__pycache__
 #| | | |-test_analysis_server.cpython-310-pytest-7.1.2.pyc
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
 #| | |-analysis_server.py
 #| | |-tracker.log
 #| | |-__pycache__
 #| | | |-analysis_server.cpython-310.pyc
COPY data_analysis/src/ api/
#COPY api/ api/

RUN mkdir -p /app/data

ENV FLASK_APP=api/app.py
ENV FLASK_ENV=production
ENV DB_PATH=/app/data/exchange_rates.db

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "api.analysis_server:app"]
