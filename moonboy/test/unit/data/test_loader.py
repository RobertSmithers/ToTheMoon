import os
import shutil
import tempfile
import pandas as pd
import pytest
from datetime import datetime
from unittest.mock import MagicMock

from moonboy.data.loader import (
    scan_cache_ranges, find_missing_ranges, get_split_ranges, load_data, save_data, parse_date, get_fname
)

def make_test_csv(path, dates):
    df = pd.DataFrame({
        'Date': dates,
        'Open': range(len(dates)),
        'High': range(len(dates)),
        'Low': range(len(dates)),
        'Close': range(len(dates)),
        'Volume': range(len(dates)),
        'Dividends': [0]*len(dates),
        'Stock Splits': [0]*len(dates),
    })
    df = df.set_index('Date')
    df.to_csv(path)

class DummyVendor:
    def get_historical_data(self, ticker, interval, start, end, **kwargs):
        # Return a DataFrame with one row per day in the range
        idx = pd.date_range(start=parse_date(start), end=parse_date(end)-pd.Timedelta(days=1), freq='D')
        if len(idx) == 0:
            return pd.DataFrame()
        df = pd.DataFrame({
            'Open': range(len(idx)),
            'High': range(len(idx)),
            'Low': range(len(idx)),
            'Close': range(len(idx)),
            'Volume': range(len(idx)),
            'Dividends': [0]*len(idx),
            'Stock Splits': [0]*len(idx),
        }, index=idx)
        return df

@pytest.fixture(scope='function')
def temp_cache_dir(monkeypatch):
    tmpdir = tempfile.mkdtemp()
    monkeypatch.setattr('moonboy.data.loader.os.path.dirname', lambda _: tmpdir)
    monkeypatch.setattr('moonboy.data.loader.os.path.exists', os.path.exists)
    monkeypatch.setattr('moonboy.data.loader.os.makedirs', os.makedirs)
    monkeypatch.setattr('moonboy.data.loader.os.listdir', os.listdir)
    yield tmpdir
    shutil.rmtree(tmpdir)

def test_scan_cache_ranges_and_find_missing(temp_cache_dir):
    ticker = 'AAPL'
    interval = '1d'
    cache_dir = os.path.join(temp_cache_dir, 'historical')
    os.makedirs(os.path.join(cache_dir, ticker), exist_ok=True)
    # Create two cached files: 2020-01-01 to 2020-07-01 (exclusive), 2020-07-01 to 2021-01-01 (exclusive)
    make_test_csv(get_fname(ticker, interval, '2020-01-01', '2020-07-01', cache_dir=cache_dir), pd.date_range('2020-01-01', '2020-06-30', freq='D'))
    make_test_csv(get_fname(ticker, interval, '2020-07-01', '2021-01-01', cache_dir=cache_dir), pd.date_range('2020-07-01', '2020-12-31', freq='D'))
    print("[TEST DEBUG] Files in cache dir:", os.listdir(os.path.join(cache_dir, ticker)))
    cached = scan_cache_ranges(ticker, interval, cache_dir)
    assert len(cached) == 2
    # Request 2020-03-01 to 2020-09-01
    missing = find_missing_ranges('2020-03-01', '2020-09-01', cached)
    # Should be empty (fully covered)
    assert missing == []
    # Request 2019-12-01 to 2020-02-01
    missing = find_missing_ranges('2019-12-01', '2020-02-01', cached)
    assert len(missing) == 1
    assert missing[0].start == parse_date('2019-12-01')
    assert missing[0].end == parse_date('2020-01-01')
    # Request 2021-01-01 to 2021-02-01
    missing = find_missing_ranges('2021-01-01', '2021-02-01', cached)
    assert len(missing) == 1
    assert missing[0].start == parse_date('2021-01-01')
    assert missing[0].end == parse_date('2021-02-01')

def test_get_split_ranges():
    # 1d interval should split by year
    ranges = get_split_ranges('2020-01-01', '2022-06-01', '1d')
    assert len(ranges) == 3
    assert ranges[0].start.year == 2020
    assert ranges[1].start.year == 2021
    assert ranges[2].start.year == 2022
    # 1h interval should split by month
    ranges = get_split_ranges('2020-01-01', '2020-04-01', '1h')
    assert len(ranges) == 3  # Jan, Feb, Mar
    assert ranges[0].start.month == 1
    assert ranges[1].start.month == 2
    assert ranges[2].start.month == 3

def test_load_data_smart(temp_cache_dir):
    ticker = 'AAPL'
    interval = '1d'
    vendor = DummyVendor()
    cache_dir = os.path.join(temp_cache_dir, 'historical')
    os.makedirs(os.path.join(cache_dir, ticker), exist_ok=True)
    # Should download and cache 2020 and 2021 as separate files
    df = load_data(vendor, ticker, interval, '2020-01-01', '2021-12-31', cache_dir=cache_dir)
    assert not df.empty
    assert df.index.min() == parse_date('2020-01-01')
    assert df.index.max() == parse_date('2021-12-30')
    # Should not re-download if called again
    df2 = load_data(vendor, ticker, interval, '2020-01-01', '2021-12-31', cache_dir=cache_dir)
    assert df2.equals(df)
    # Should only download missing range if we extend
    df3 = load_data(vendor, ticker, interval, '2019-01-01', '2021-12-31', cache_dir=cache_dir)
    assert parse_date('2019-01-01') in df3.index
    assert df3.index.min() == parse_date('2019-01-01')
