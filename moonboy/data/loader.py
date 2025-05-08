# This file downloads historical data to be used for backtesting.
# It uses the yfinance library to download data from Yahoo Finance.

import yfinance as yf
import pandas as pd
import os
from utils.file_management import get_fname
from datetime import datetime
from vendors.vendor_interface import SecuritiesVendor
from typing import Union

def download_data(
    vendor: SecuritiesVendor,
    ticker: str,
    interval: str,
    start_date: Union[str, datetime],
    end_date: Union[str, datetime],
    cache_data: bool = True,
    **kwargs
) -> pd.DataFrame:
    """
    Download historical data for a given ticker from the specified vendor.

    Parameters:
    vendor (SecuritiesVendor): The data vendor to use
    ticker (str): The stock ticker symbol
    interval (str): The data interval (e.g., '1d', '1h', '1m')
    start_date (str/datetime): The start date for the data
    end_date (str/datetime): The end date for the data
    cache_data (bool): Whether to cache the downloaded data
    **kwargs: Additional parameters to pass to the vendor

    Returns:
    pd.DataFrame: A DataFrame containing the historical data
    """
    data = vendor.get_historical_data(ticker, interval, start_date, end_date, **kwargs)

    # Cache downloaded data if requested
    if cache_data:
        fname = get_fname(ticker, interval, start_date, end_date)
        save_data(data, fname)

    return data

def save_data(data: pd.DataFrame, filename: str) -> None:
    """
    Save the historical data to a CSV file.

    Parameters:
    data (pd.DataFrame): The DataFrame containing the historical data.
    filename (str): The name of the file to save the data to.
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    data.to_csv(filename, index=True)
    print(f"Data saved to {filename}")

def load_data(
    vendor: SecuritiesVendor,
    ticker: str,
    interval: str,
    start_date: Union[str, datetime],
    end_date: Union[str, datetime],
    cache_data: bool = True,
    **kwargs
) -> pd.DataFrame:
    """
    Load historical data from a CSV file or download if not present.

    Parameters:
    vendor (SecuritiesVendor): The data vendor to use if download is needed
    ticker (str): The stock ticker symbol
    interval (str): The data interval (e.g., '1d', '1h', '1m')
    start_date (str/datetime): The start date for the data
    end_date (str/datetime): The end date for the data
    cache_data (bool): Whether to cache downloaded data
    **kwargs: Additional parameters to pass to the vendor

    Returns:
    pd.DataFrame: A DataFrame containing the historical data
    """
    fname = get_fname(ticker, interval, start_date, end_date)
    if not os.path.exists(fname):
        return download_data(vendor, ticker, interval, start_date, end_date, cache_data, **kwargs)
    return pd.read_csv(fname, index_col=0, parse_dates=True)