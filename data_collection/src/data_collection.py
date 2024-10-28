import requests
import json
from datetime import datetime, timedelta
import logging
from sqlalchemy import create_engine, Column, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import sys
from pathlib import Path
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('tracker.log'), logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

DB_PATH = os.getenv('DB_PATH', 'exchange_rates.db')
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
Base = declarative_base()

class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    country_currency_desc = Column(String, primary_key=True)
    exchange_rate = Column(Float)
    record_date = Column(Date, primary_key=True)
    def __repr__(self):
        return f"<ExchangeRate(country='{self.country_currency_desc}', rate={self.exchange_rate}, date={self.record_date})>"

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

def get_latest_date(session):
    latest_date = session.query(func.max(ExchangeRate.record_date)).scalar()
    if latest_date:
        return latest_date.strftime("%Y-%m-%d")
    logger.info("No latest starting date")
    return '2010-01-01'

def fetch_exchange_rates():
    session = Session()
    latest_date = get_latest_date(session)
    session.close()
    logger.info(f"Latest date: {latest_date}")
    countries = [
        'Australia-Dollar',
        'Canada-Dollar',
        'Mexico-Peso',
        'Germany-Euro',
        'United Kingdom-Pound'
    ]
    countries_param = ','.join(countries)
    url = f"https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/rates_of_exchange"
    try:
        params = {
            'fields': 'country_currency_desc,exchange_rate,record_date',
            'filter': f'country_currency_desc:in:({countries_param}),record_date:gte:{latest_date}',
            'page[size]': 10000 
        }
        response = requests.get(url, params=params)
        response.raise_for_status() 
        logger.info(f"Made request")
        data = response.json()

        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed with status code {str(e)}")
        raise 

def save_to_database(data, session):
    new_entries = 0
    try:
        for record in data['data']:
            exchange_rate = ExchangeRate(
                country_currency_desc=record['country_currency_desc'],
                exchange_rate=float(record['exchange_rate']),
                record_date=datetime.strptime(record['record_date'], '%Y-%m-%d').date()
            )
            try:
                session.merge(exchange_rate)
                new_entries += 1
            except:
                session.rollback()
                continue

        session.commit()
        logger.info("Saved to database")
        return new_entries
    except: 
        logger.error("Unable to save to database")

if __name__ == "__main__":
    try:
        data = fetch_exchange_rates()
        session = Session()
        new_entries = save_to_database(data, session)
        session.close()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
