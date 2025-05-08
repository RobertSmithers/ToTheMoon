
def get_fname(ticker, interval, start_dt, end_dt):
    """
    Get the filename for a ticker's historical data.
    """
    return f'data/historical/{ticker}/{interval}-{start_dt}-{end_dt}.csv'