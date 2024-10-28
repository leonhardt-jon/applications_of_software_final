from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, String, Float, Date
import os
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent / "data_collection" / "src"
sys.path.append(str(src_path))


Base = declarative_base()
class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    country_currency_desc = Column(String, primary_key=True)
    exchange_rate = Column(Float)
    record_date = Column(Date, primary_key=True)
    def __repr__(self):
        return f"<ExchangeRate(country='{self.country_currency_desc}', rate={self.exchange_rate}, date={self.record_date})>"

app = Flask(__name__)
CORS(app) 


DB_PATH = os.getenv('DB_PATH', 'exchange_rates.db')
engine = create_engine(f'sqlite:///{DB_PATH}')
Session = sessionmaker(bind=engine)

def _get_currencies(session):
    try:
        currencies = session.query(ExchangeRate.country_currency_desc)\
            .distinct()\
            .all()
        return jsonify([currency[0] for currency in currencies])
    finally:
        session.close()

@app.route('/api/currencies', methods=['GET'])
def get_currencies():
    """Get list of available currencies"""
    session = Session()
    return _get_currencies(session)

@app.route('/api/rates/<currency>', methods=['GET'])
def get_rates(currency):
    """Get exchange rates for a specific currency"""
    session = Session()
    try:
        # Get rates for the last 12 months
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=365*5)
        
        rates = session.query(ExchangeRate)\
            .filter(
                ExchangeRate.country_currency_desc == currency,
                ExchangeRate.record_date >= start_date
            )\
            .order_by(ExchangeRate.record_date)\
            .all()
        
        return jsonify([{
            'date': rate.record_date.isoformat(),
            'rate': rate.exchange_rate
        } for rate in rates])
    finally:
        session.close()

@app.route('/api/latest', methods=['GET'])
def get_latest_rates():
    """Get latest exchange rates for all currencies"""
    session = Session()
    try:
        # Get the most recent date
        latest_date = session.query(ExchangeRate.record_date)\
            .order_by(desc(ExchangeRate.record_date))\
            .first()[0]
        
        # Get rates for all currencies on that date
        rates = session.query(ExchangeRate)\
            .filter(ExchangeRate.record_date == latest_date)\
            .all()
        
        return jsonify([{
            'currency': rate.country_currency_desc,
            'rate': rate.exchange_rate,
            'date': rate.record_date.isoformat()
        } for rate in rates])
    finally:
        session.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
