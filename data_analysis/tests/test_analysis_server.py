import pytest 
from datetime import datetime, timedelta
import json 
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session 
from pathlib import Path 
import sys 

src_path = Path(__file__).parent.parent / "src"
sys.path.append(str(src_path))

from analysis_server import app, Session as DBSession
from data_collection import ExchangeRate


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client



@pytest.fixture
def mock_db_session():
    mock_session = Mock(spec=Session)
    #original_session = DBSession
    DBSession = Mock(return_value=mock_session)
    yield mock_session
    
    #DBSession = original_session


def create_mock_exchange_rate(country, rate, date):
    mock_rate = Mock(spec=ExchangeRate)
    mock_rate.country_currency_desc = country
    mock_rate.exchange_rate = rate
    mock_rate.record_date = date
    return mock_rate

class TestCurrencyAPI:
    def test_get_currencies(self, client, mock_db_session):
        mock_currencies = [
            ('Australia-Dollar',),
            ('Canada-Dollar',),
            ('Mexico-Peso',),
            ('Germany-Euro',),
            ('United Kingdom-Pound',),
        ]
        
        mock_query = Mock()
        mock_query.distinct.return_value.all.return_value = mock_currencies
        mock_db_session.query.return_value = mock_query
        
        response = client.get('/api/currencies')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == len(mock_currencies)
        assert 'Canada-Dollar' in data
        assert 'Mexico-Peso' in data
        assert 'Germany-Euro' in data
        assert 'Australia-Dollar' in data
        assert 'United Kingdom-Pound' in data

    def test_get_rates_for_currency(self, client, mock_db_session):
        currency = 'Canada-Dollar'
        today = datetime.now().date()
        
        mock_rates = [
            create_mock_exchange_rate(currency, 0.75, today - timedelta(days=2)),
            create_mock_exchange_rate(currency, 0.76, today - timedelta(days=1)),
            create_mock_exchange_rate(currency, 0.77, today)
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_rates
        mock_db_session.query.return_value = mock_query
        
        response = client.get(f'/api/rates/{currency}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) > 0
        assert all(isinstance(rate['rate'], (int, float)) for rate in data)
        assert all(isinstance(rate['date'], str) for rate in data)

    def test_get_rates_no_data(self, client, mock_db_session):
        currency = 'Nonexistent-Currency'
        
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        response = client.get(f'/api/rates/{currency}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 0
        
    def test_get_latest_rates(self, client, mock_db_session):
        """Test the /api/latest endpoint"""
        today = datetime.now().date()
        
        mock_rates = [
            create_mock_exchange_rate('Canada-Dollar', 0.75, today),
            create_mock_exchange_rate('Mexico-Peso', 0.059, today),
        ]
        
        mock_date_query = Mock()
        mock_date_query.order_by.return_value.first.return_value = (today,)
        
        mock_rates_query = Mock()
        mock_rates_query.filter.return_value.all.return_value = mock_rates
        
        mock_db_session.query.side_effect = [mock_date_query, mock_rates_query]
        
        response = client.get('/api/latest')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert any(rate['currency'] == 'Canada-Dollar' for rate in data)
        assert any(rate['currency'] == 'Mexico-Peso' for rate in data)
        

        


if __name__ == '__main__':
    pytest.main([__file__])
