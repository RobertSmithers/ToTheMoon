import backtrader as bt
from strategies.baseline_strategy import MovingAverageCrossover
from datetime import datetime
import os
from dotenv import load_dotenv
import pandas as pd

# Import our data vendors
from trading_agent.data.vendors.yahoo.yahoo_vendor import YahooFinanceVendor
from trading_agent.data.vendors.polygon.polygon_vendor import PolygonVendor
from trading_agent.data.loader import load_data

# Load environment variables
load_dotenv()

# Configuration
CONFIG = {
    'ticker': 'AAPL',  # Stock to backtest
    'interval': '1d',  # Data interval (1m, 5m, 15m, 30m, 1h, 1d, 1w, 1mo)
    'start_date': '2023-01-01',
    'end_date': '2024-01-01',
    'vendor': 'yahoo',  # 'yahoo' or 'polygon'
    'cache_data': True,  # Whether to cache downloaded data
}

class PandasData(bt.feeds.PandasData):
    """Custom data feed for Backtrader that works with our vendor data format."""
    params = (
        ('datetime', None),  # Use index as datetime
        ('open', 'Open'),
        ('high', 'High'),
        ('low', 'Low'),
        ('close', 'Close'),
        ('volume', 'Volume'),
        ('openinterest', None),
    )

def get_vendor():
    """Initialize and return the appropriate data vendor."""
    if CONFIG['vendor'].lower() == 'yahoo':
        return YahooFinanceVendor()
    elif CONFIG['vendor'].lower() == 'polygon':
        api_key = os.getenv('POLYGON_API_KEY')
        if not api_key:
            raise ValueError("POLYGON_API_KEY not found in environment variables")
        return PolygonVendor(api_key=api_key)
    else:
        raise ValueError(f"Unknown vendor: {CONFIG['vendor']}")

def main():
    # Create a Backtrader engine
    cerebro = bt.Cerebro()

    # Get the appropriate vendor
    vendor = get_vendor()
    
    # Load data using the loader
    data = load_data(
        vendor=vendor,
        ticker=CONFIG['ticker'],
        interval=CONFIG['interval'],
        start_date=CONFIG['start_date'],
        end_date=CONFIG['end_date'],
        cache_data=CONFIG['cache_data']
    )
    
    # Create Backtrader data feed
    data_feed = PandasData(dataname=data)
    cerebro.adddata(data_feed)

    # Add the strategy
    cerebro.addstrategy(MovingAverageCrossover)

    # Set initial capital
    cerebro.broker.setcash(100000.0)
    
    # Set commission
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission

    # Print initial portfolio value
    print(f'Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}')

    # Run the backtest
    print("Starting Backtest...")
    cerebro.run()
    print("Backtest Complete.")

    # Print final portfolio value
    print(f'Final Portfolio Value: ${cerebro.broker.getvalue():.2f}')

    # Plot the results
    cerebro.plot(style='candlestick')

if __name__ == '__main__':
    main()