# This file downloads historical data to be used for backtesting.
# It uses the yfinance library to download data from Yahoo Finance.

import yfinance as yf
import pandas as pd
import os
from datetime import datetime
from typing import Union
import logging
import re
from dateutil import parser as date_parser
from collections import namedtuple

from moonboy.data.vendors.vendor_interface import SecuritiesVendor
from moonboy.utils.file_management import get_fname as _get_fname

# Set up logger
logger = logging.getLogger(__name__)

# --- SMART LOADER UTILS ---
# How to split files for each interval (e.g., 1d: yearly, 1h: monthly)
INTERVAL_SPLIT = {
    '1d': 'year',
    '1h': 'month',
    '1wk': 'year',
    '1mo': 'decade',
    '5d': 'year',
    '30m': 'month',
    '15m': 'month',
    '5m': 'month',
    '1m': 'month',
}

Range = namedtuple('Range', ['start', 'end'])

def parse_date(date_str):
    if isinstance(date_str, datetime):
        return date_str
    return date_parser.parse(str(date_str))

def get_split_ranges(start, end, interval):
    """
    Given a start and end datetime, and interval, return a list of (split_start, split_end) tuples
    according to the INTERVAL_SPLIT granularity.
    """
    start = parse_date(start)
    end = parse_date(end)
    split = INTERVAL_SPLIT.get(interval, 'year')
    ranges = []
    cur = start
    while cur < end:
        if split == 'year':
            next_split = datetime(cur.year + 1, 1, 1)
        elif split == 'month':
            if cur.month == 12:
                next_split = datetime(cur.year + 1, 1, 1)
            else:
                next_split = datetime(cur.year, cur.month + 1, 1)
        elif split == 'decade':
            next_split = datetime((cur.year // 10 + 1) * 10, 1, 1)
        else:
            next_split = end
        split_end = min(next_split, end)
        ranges.append(Range(cur, split_end))
        cur = split_end
    return ranges

def scan_cache_ranges(ticker, interval, cache_dir):
    """
    Scan the cache directory for all files for a ticker/interval, returning a list of (start, end, filename).
    """
    ticker_dir = os.path.join(cache_dir, ticker)
    if not os.path.exists(ticker_dir):
        print(f"[DEBUG] Ticker dir does not exist: {ticker_dir}")
        return []
    files = os.listdir(ticker_dir)
    # Match filenames like 1d-2020-07-01-2020-12-31.csv
    pattern = re.compile(rf"{re.escape(interval)}-([0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}})-([0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}})\.csv")
    print(f"[DEBUG] scan_cache_ranges pattern: {pattern.pattern}")
    print(f"[DEBUG] scan_cache_ranges files: {files}")
    found = []
    for fname in files:
        m = pattern.fullmatch(fname)
        if m:
            s, e = m.group(1), m.group(2)
            try:
                s_dt = parse_date(s)
                e_dt = parse_date(e)
                found.append((s_dt, e_dt, os.path.join(ticker_dir, fname)))
            except Exception as ex:
                print(f"[DEBUG] Failed to parse dates from {fname}: {ex}")
                continue
        else:
            print(f"[DEBUG] Filename did not match: {fname}")
    return found

def find_missing_ranges(requested_start, requested_end, cached_ranges):
    """
    Given a requested range and a list of cached (start, end), return a list of missing (start, end) subranges.
    """
    requested_start = parse_date(requested_start)
    requested_end = parse_date(requested_end)
    # Sort and merge cached ranges
    cached = sorted([Range(parse_date(s), parse_date(e)) for s, e, _ in cached_ranges], key=lambda r: r.start)
    merged = []
    for r in cached:
        if not merged or r.start > merged[-1].end:
            merged.append(r)
        else:
            merged[-1] = Range(merged[-1].start, max(merged[-1].end, r.end))
    # Find missing
    missing = []
    cur = requested_start
    for r in merged:
        if cur < r.start:
            missing.append(Range(cur, min(r.start, requested_end)))
        cur = max(cur, r.end)
        if cur >= requested_end:
            break
    if cur < requested_end:
        missing.append(Range(cur, requested_end))
    return missing

def download_data(
    vendor: SecuritiesVendor,
    ticker: str,
    interval: str,
    start_date: Union[str, datetime],
    end_date: Union[str, datetime],
    cache_data: bool = True,
    cache_dir: str = None,
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
    cache_dir (str): The directory to cache the data in
    **kwargs: Additional parameters to pass to the vendor

    Returns:
    pd.DataFrame: A DataFrame containing the historical data
    """
    data = vendor.get_historical_data(ticker, interval, start_date, end_date, **kwargs)

    # Cache downloaded data if requested
    if cache_data:
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), 'historical')
        fname = get_fname(ticker, interval, start_date, end_date, cache_dir=cache_dir)
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        if not os.path.exists(fname):
            save_data(data, fname)

    return data

def save_data(data: pd.DataFrame, filename: str) -> None:
    """
    Save the historical data to a CSV file.

    Parameters:
    data (pd.DataFrame): The DataFrame containing the historical data.
    filename (str): The name of the file to save the data to.
    """
    # Ensure the directory exists (redundant but safe)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    # Ensure the index is named 'Date' for consistency
    if data.index.name != 'Date':
        data.index.name = 'Date'
    data.to_csv(filename, index=True)
    logger.info("Data saved to %s", filename)

def get_fname(ticker, interval, start_dt, end_dt, cache_dir=None):
    from pathlib import Path
    # Ensure start_dt and end_dt are date-only strings
    if hasattr(start_dt, 'strftime'):
        start_dt = start_dt.strftime('%Y-%m-%d')
    if hasattr(end_dt, 'strftime'):
        end_dt = end_dt.strftime('%Y-%m-%d')
    if cache_dir is None:
        return _get_fname(ticker, interval, start_dt, end_dt)
    return str(Path(cache_dir) / ticker / f'{interval}-{start_dt}-{end_dt}.csv')

def load_data(
    vendor: SecuritiesVendor,
    ticker: str,
    interval: str,
    start_date: Union[str, datetime],
    end_date: Union[str, datetime],
    cache_data: bool = True,
    cache_dir: str = None,
    **kwargs
) -> pd.DataFrame:
    """
    Load historical data from cache, downloading only missing subranges, and merging all relevant data.
    """
    if cache_dir is None:
        cache_dir = os.path.join(os.path.dirname(__file__), 'historical')
    # 1. Scan cache for all files for this ticker/interval
    cached = scan_cache_ranges(ticker, interval, cache_dir)
    # 2. Find missing subranges
    missing = find_missing_ranges(start_date, end_date, cached)
    # 3. Download and cache missing subranges, split by year/month/etc
    new_files = []
    for rng in missing:
        for split_rng in get_split_ranges(rng.start, rng.end, interval):
            # Use exclusive end date in filename
            fname = get_fname(ticker, interval, split_rng.start.date(), split_rng.end.date(), cache_dir=cache_dir)
            if not os.path.exists(fname):
                df = download_data(vendor, ticker, interval, split_rng.start, split_rng.end, cache_data=True, cache_dir=cache_dir, **kwargs)
                if not df.empty:
                    save_data(df, fname)
                    new_files.append((split_rng.start, split_rng.end, fname))
    # 4. Gather all relevant files (old + new) that overlap the requested range
    all_files = [f for f in cached] + new_files
    relevant_files = [f for f in all_files if not (f[1] <= parse_date(start_date) or f[0] >= parse_date(end_date))]
    # 5. Load, merge, deduplicate
    dfs = []
    for s, e, fname in relevant_files:
        df = pd.read_csv(fname, index_col=0, parse_dates=True)
        if df.index.name != 'Date':
            df.index.name = 'Date'
        dfs.append(df)
    if dfs:
        full_df = pd.concat(dfs)
        full_df = full_df[~full_df.index.duplicated(keep='last')]
        # Filter to requested range
        full_df = full_df[(full_df.index >= parse_date(start_date)) & (full_df.index < parse_date(end_date))]
        full_df = full_df.sort_index()
        logger.info("Loaded %d rows of data for %s from %s to %s with interval %s (smart cache)", len(full_df), ticker, start_date, end_date, interval)
        return full_df
    else:
        logger.warning("No data found for %s from %s to %s with interval %s", ticker, start_date, end_date, interval)
        return pd.DataFrame()
