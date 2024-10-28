#!/bin/bash
echo "Running initial currency data update..."
python /app/data_collection/src/data_collection.py >> /var/log/cron.log 2>&1

echo "Starting cron daemon..."
cron

tail -f /var/log/cron.log

