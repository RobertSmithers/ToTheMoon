from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Union
import pandas as pd

class SecuritiesVendor(ABC):
    """Abstract base class for securities data vendors.
    
    This class defines the standard interface that all securities data vendors must implement.
    It provides methods for retrieving historical market data and other common operations.
    """
    
    @abstractmethod
    def get_historical_data(
        self,
        ticker: str,
        interval: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        **kwargs
    ) -> pd.DataFrame:
        """Retrieve historical market data for a given ticker.
        
        Args:
            ticker: The security ticker symbol
            interval: The data interval (e.g., '1d', '1h', '1m')
            start_date: Start date for the data range
            end_date: End date for the data range
            **kwargs: Additional vendor-specific parameters
            
        Returns:
            DataFrame containing the historical data with standard columns:
            - Open, High, Low, Close, Volume
            - Index should be datetime
        """
        pass
    
    @abstractmethod
    def get_current_price(self, ticker: str) -> float:
        """Get the current price for a given ticker.
        
        Args:
            ticker: The security ticker symbol
            
        Returns:
            Current price as float
        """
        pass
    
    @abstractmethod
    def get_company_info(self, ticker: str) -> dict:
        """Get basic company information.
        
        Args:
            ticker: The security ticker symbol
            
        Returns:
            Dictionary containing company information such as:
            - name
            - sector
            - industry
            - market_cap
            - etc.
        """
        pass
    
    @abstractmethod
    def validate_ticker(self, ticker: str) -> bool:
        """Validate if a ticker symbol exists and is valid.
        
        Args:
            ticker: The security ticker symbol to validate
            
        Returns:
            True if ticker is valid, False otherwise
        """
        pass
    
    @staticmethod
    def standardize_interval(interval: str) -> str:
        """Convert interval string to standardized format.
        
        Args:
            interval: Input interval string (e.g., '1d', '1day', 'daily')
            
        Returns:
            Standardized interval string
        """
        interval = interval.lower()
        interval_map = {
            '1m': '1m', '1min': '1m', 'minute': '1m',
            '5m': '5m', '5min': '5m',
            '15m': '15m', '15min': '15m',
            '30m': '30m', '30min': '30m',
            '1h': '1h', '1hour': '1h', 'hourly': '1h',
            '1d': '1d', '1day': '1d', 'daily': '1d',
            '1w': '1w', '1week': '1w', 'weekly': '1w',
            '1mo': '1mo', '1month': '1mo', 'monthly': '1mo'
        }
        return interval_map.get(interval, interval)
    
    @staticmethod
    def standardize_dates(
        start_date: Union[str, datetime],
        end_date: Union[str, datetime]
    ) -> tuple[datetime, datetime]:
        """Convert date inputs to standardized datetime objects.
        
        Args:
            start_date: Start date as string or datetime
            end_date: End date as string or datetime
            
        Returns:
            Tuple of (start_date, end_date) as datetime objects
        """
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        return start_date, end_date
