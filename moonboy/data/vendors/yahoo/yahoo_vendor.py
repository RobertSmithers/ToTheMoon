import yfinance as yf
from datetime import datetime
from typing import Union
import pandas as pd
import requests
import logging
import os
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Configure logging
logger = logging.getLogger(__name__)

# Disable SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from ..vendor_interface import SecuritiesVendor
from moonboy.utils.file_management import get_fname

class YahooFinanceVendor(SecuritiesVendor):
    """Yahoo Finance implementation of the SecuritiesVendor interface."""
    
    def __init__(self):
        """Initialize the vendor with a custom session."""
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification
        # yf.pdr_override()  # Override pandas_datareader with yfinance
    
    def get_historical_data(
        self,
        ticker: str,
        interval: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        **kwargs
    ) -> pd.DataFrame:
        """Retrieve historical market data from Yahoo Finance.
        
        Args:
            ticker: The security ticker symbol
            interval: The data interval (e.g., '1d', '1h', '1m')
            start_date: Start date for the data range
            end_date: End date for the data range
            **kwargs: Additional parameters passed to yfinance
            
        Returns:
            DataFrame containing the historical data
        """
        # Standardize inputs
        interval = self.standardize_interval(interval)
        start_date, end_date = self.standardize_dates(start_date, end_date)
        
        # Check if data exists in cache
        fname = get_fname(ticker, interval, start_date, end_date)
        if os.path.exists(fname):
            logger.info("Loading cached data from %s", fname)
            return pd.read_csv(fname, index_col=0, parse_dates=True)
        
        # Download data if not in cache
        logger.info("Downloading data for %s from %s to %s with interval %s", ticker, start_date, end_date, interval)
        ticker_obj = yf.Ticker(ticker)
        data = ticker_obj.history(
            start=start_date,
            end=end_date,
            interval=interval,
            **kwargs
        )

        logger.info("Loaded %d rows of data for %s from %s to %s with interval %s", len(data), ticker, start_date, end_date, interval)
        
        return data
    
    def get_current_price(self, ticker: str) -> float:
        """Get the current price from Yahoo Finance.
        
        Args:
            ticker: The security ticker symbol
            
        Returns:
            Current price as float
        """
        ticker_obj = yf.Ticker(ticker)
        return ticker_obj.info.get('regularMarketPrice', 0.0)
    
    def get_company_info(self, ticker: str) -> dict:
        """Get company information from Yahoo Finance.
        
        Args:
            ticker: The security ticker symbol
            
        Returns:
            Dictionary containing company information
        """
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        
        return {
            'name': info.get('longName', ''),
            'sector': info.get('sector', ''),
            'industry': info.get('industry', ''),
            'market_cap': info.get('marketCap', 0),
            'currency': info.get('currency', ''),
            'exchange': info.get('exchange', ''),
            'country': info.get('country', ''),
            'website': info.get('website', ''),
            'description': info.get('longBusinessSummary', '')
        }
    
    def validate_ticker(self, ticker: str) -> bool:
        """Validate if a ticker symbol exists on Yahoo Finance.
        
        Args:
            ticker: The security ticker symbol to validate
            
        Returns:
            True if ticker is valid, False otherwise
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            # Try to get basic info to validate
            info = ticker_obj.info
            return bool(info.get('regularMarketPrice'))
        except Exception:
            return False 