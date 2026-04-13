import pytest
from unittest.mock import patch, MagicMock
from src.collect_data.gas_prices import fetch_ttf_gas_prices

@patch('yfinance.Ticker')
def test_fetch_ttf_gas_prices_success(mock_ticker):
    # Mocking yfinance response
    mock_df = MagicMock()
    mock_df.empty = False
    mock_df.iloc = [None] # Dummy for indexing
    mock_df.iloc[-1] = {'Open': 100, 'High': 110, 'Low': 90, 'Close': 105, 'Volume': 1000}
    
    mock_ticker.return_value.history.return_value = mock_df
    
    result = fetch_ttf_gas_prices()
    
    assert result is not None
    assert result[0]['price_close'] == 105.0
    assert result[0]['commodity'] == "TTF_GAS"