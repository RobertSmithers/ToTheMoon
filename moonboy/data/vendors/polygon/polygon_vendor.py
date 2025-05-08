from datetime import datetime
from typing import Union
import pandas as pd
from polygon import RESTClient
import os

from ..vendor_interface import SecuritiesVendor

class PolygonVendor(SecuritiesVendor):
    """Polygon.io implementation of the SecuritiesVendor interface."""
    
    def __init__(self, api_key: str = None):
        """Initialize the Polygon.io client.
        
        Args:
            api_key: Polygon.io API key. If not provided, will look for POLYGON_API_KEY env var.
        """
        self.api_key = api_key or os.getenv('POLYGON_API_KEY')
        if not self.api_key:
            raise ValueError("Polygon.io API key is required")
        self.client = RESTClient(self.api_key)
    
    def get_historical_data(
        self,
        ticker: str,
        interval: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        **kwargs
    ) -> pd.DataFrame:
        """Retrieve historical market data from Polygon.io.
        
        Args:
            ticker: The security ticker symbol
            interval: The data interval (e.g., '1d', '1h', '1m')
            start_date: Start date for the data range
            end_date: End date for the data range
            **kwargs: Additional parameters passed to Polygon.io
            
        Returns:
            DataFrame containing the historical data
        """
        # Standardize inputs
        interval = self.standardize_interval(interval)
        start_date, end_date = self.standardize_dates(start_date, end_date)
        
        # Convert interval to Polygon.io format
        multiplier, timespan = self._convert_interval(interval)
        
        # Get aggregates
        aggs = self.client.get_aggs(
            ticker,
            multiplier,
            timespan,
            start_date,
            end_date,
            **kwargs
        )
        
        # Convert to DataFrame
        data = pd.DataFrame([{
            'Open': agg.open,
            'High': agg.high,
            'Low': agg.low,
            'Close': agg.close,
            'Volume': agg.volume
        } for agg in aggs])
        
        # Set index
        data.index = pd.to_datetime([agg.timestamp for agg in aggs])
        
        return data
    
    def get_current_price(self, ticker: str) -> float:
        """Get the current price from Polygon.io.
        
        Args:
            ticker: The security ticker symbol
            
        Returns:
            Current price as float
        """
        last_trade = self.client.get_last_trade(ticker)
        return float(last_trade.price)
    
    def get_company_info(self, ticker: str) -> dict:
        """Get company information from Polygon.io.
        
        Args:
            ticker: The security ticker symbol
            
        Returns:
            Dictionary containing company information
        """
        ticker_details = self.client.get_ticker_details(ticker)
        
        return {
            'name': ticker_details.name,
            'sector': ticker_details.sector,
            'industry': ticker_details.industry,
            'market_cap': ticker_details.market_cap,
            'currency': ticker_details.currency_name,
            'exchange': ticker_details.primary_exchange,
            'country': ticker_details.locale,
            'website': ticker_details.homepage_url,
            'description': ticker_details.description
        }
    
    def validate_ticker(self, ticker: str) -> bool:
        """Validate if a ticker symbol exists on Polygon.io.
        
        Args:
            ticker: The security ticker symbol to validate
            
        Returns:
            True if ticker is valid, False otherwise
        """
        try:
            self.client.get_ticker_details(ticker)
            return True
        except Exception:
            return False
    
    def _convert_interval(self, interval: str) -> tuple[int, str]:
        """Convert standardized interval to Polygon.io format.
        
        Args:
            interval: Standardized interval string (e.g., '1m', '1h', '1d')
            
        Returns:
            Tuple of (multiplier, timespan)
        """
        interval_map = {
            '1m': (1, 'minute'),
            '5m': (5, 'minute'),
            '15m': (15, 'minute'),
            '30m': (30, 'minute'),
            '1h': (1, 'hour'),
            '1d': (1, 'day'),
            '1w': (1, 'week'),
            '1mo': (1, 'month')
        }
        return interval_map.get(interval, (1, 'day')) 