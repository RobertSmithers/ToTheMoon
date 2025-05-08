from pathlib import Path
import os

def get_fname(ticker, interval, start_dt, end_dt, cache_dir=None):
    """
    Get the filename for a ticker's historical data.
    Returns a full path starting from the moonboy package directory or a custom cache_dir if provided.
    """
    if cache_dir is None:
        # Get the moonboy package directory (where this file is located)
        package_dir = Path(__file__).parent.parent
        cache_dir = package_dir / 'data' / 'historical'
    else:
        cache_dir = Path(cache_dir)
    # Construct the full path
    return str(cache_dir / ticker / f'{interval}-{start_dt}-{end_dt}.csv')