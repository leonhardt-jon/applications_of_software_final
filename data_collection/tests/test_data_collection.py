import pytest
from datetime import datetime 
import sqlite3 
from unittest.mock import Mock, patch 
from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker 
import json 
import os
import sys
from pathlib import Path 

src_path = Path(__file__).parent.parent / "src"
sys.path.append(str(src_path)) 

from data_collection import (
    ExchangeRate,
    Base, 
    get_latest_date, 
    fetch_exchange_rates, 
    save_to_database
)

@pytest.fixture
def test_db():
    db_path = "test_exchange_rates.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    yield Session

    Session.close_all()
    try: 
        os.remove(db_path)
    except OSError:
        pass


@pytest.fixture
def sample_api_response():
    return {
        "data": [
            {
                "country_currency_desc": "Canada-Dollar",
                "exchange_rate": "0.75",
                "record_date": "2024-01-01"
            },
            {
                "country_currency_desc": "Mexico-Peso",
                "exchange_rate": "0.059",
                "record_date": "2024-01-01"
            },
            {
                "country_currency_desc": "Germany-Euro",
                "exchange_rate": "1.10",
                "record_date": "2024-01-01"
            }
        ]
    }

def test_get_latest_date(test_db):
    session = test_db()
    latest_date = get_latest_date(session)
    assert latest_date == "2010-01-01"
    session.close()

@patch('requests.get')
def test_fetch_exchange_rates_success(mock_get, sample_api_response):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_api_response
    mock_get.return_value = mock_response
    
    data = fetch_exchange_rates()['data']
    
    assert len(data) == 3
    assert data[0]["country_currency_desc"] == "Canada-Dollar"
    assert float(data[0]["exchange_rate"]) == 0.75
    assert data[0]["record_date"] == "2024-01-01"

@patch('requests.get') 
def test_fetch_exchange_rates_error(mock_get):
    mock_response = Mock() 
    mock_response.status_code = 404 
    mock_response.raise_for_status.side_effect = Exception("API Error") 
    mock_get.return_value = mock_response 
    with pytest.raises(Exception):
        fetch_exchange_rates()

def test_save_to_database(test_db, sample_api_response):
    session = test_db()
    new_entries = save_to_database(sample_api_response, session)
    assert new_entries == 3
    
    saved_rates = session.query(ExchangeRate).all()
    assert len(saved_rates) == 3
    
    canadian_dollar = session.query(ExchangeRate)\
        .filter_by(country_currency_desc="Canada-Dollar")\
        .first()
    assert canadian_dollar.exchange_rate == 0.75
    
    session.close()


def test_save_duplicate_data(test_db, sample_api_response):
    session = test_db()
    save_to_database(sample_api_response, session)
    new_entries = save_to_database(sample_api_response, session)
    assert new_entries == 3
    
    saved_rates = session.query(ExchangeRate).all()
    assert len(saved_rates) == 3
    
    session.close()

def test_save_invalid_data(test_db):
    session = test_db()
    invalid_data = {'data': [
        {
            "country_currency_desc": "Test-Currency",
            "exchange_rate": "invalid",  
            "record_date": "2024-01-01"
        }
        ]}
    
    new_entries = save_to_database(invalid_data, session)
    assert new_entries == None  
    
    saved_rates = session.query(ExchangeRate).all()
    assert len(saved_rates) == 0
    
    session.close()
