import backtrader as bt
from datetime import datetime
import os
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
import logging

from moonboy.strategies.baseline_strategy import MovingAverageCrossover

# Import our data vendors
from moonboy.data.vendors.yahoo.yahoo_vendor import YahooFinanceVendor
from moonboy.data.vendors.polygon.polygon_vendor import PolygonVendor
from moonboy.data.loader import load_data

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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
)

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

class PortfolioAnalyzer(bt.analyzers.Analyzer):
    """Custom analyzer to track portfolio value over time."""
    def __init__(self):
        super(PortfolioAnalyzer, self).__init__()
        self.portfolio_values = []
        self.dates = []

    def next(self):
        self.portfolio_values.append(self.strategy.broker.getvalue())
        self.dates.append(self.data.datetime.date(0))

    def get_analysis(self):
        return {
            'portfolio_values': self.portfolio_values,
            'dates': self.dates
        }

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

def plot_portfolio_performance(analyzer, strategy_name):
    """Plot portfolio value over time."""
    plt.figure(figsize=(12, 6))
    plt.plot(analyzer['dates'], analyzer['portfolio_values'])
    plt.title(f'Portfolio Value Over Time - {strategy_name}')
    plt.xlabel('Date')
    plt.ylabel('Portfolio Value ($)')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the plot
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    plot_filename = f'portfolio_performance_{strategy_name}_{timestamp}.png'
    plt.savefig(plot_filename)
    plt.close()
    return plot_filename

def print_performance_metrics(analyzer, strategy_name):
    """Print detailed performance metrics."""
    portfolio_values = analyzer['portfolio_values']
    initial_value = portfolio_values[0]
    final_value = portfolio_values[-1]
    total_return = ((final_value - initial_value) / initial_value) * 100
    
    # Calculate daily returns
    daily_returns = pd.Series(portfolio_values).pct_change().dropna()
    
    # Calculate metrics
    annualized_return = (1 + total_return/100) ** (252/len(portfolio_values)) - 1
    sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * (252 ** 0.5)
    max_drawdown = ((pd.Series(portfolio_values).cummax() - portfolio_values) / pd.Series(portfolio_values).cummax()).max() * 100
    
    print(f"\nPerformance Metrics for {strategy_name}:")
    print(f"Initial Portfolio Value: ${initial_value:,.2f}")
    print(f"Final Portfolio Value: ${final_value:,.2f}")
    print(f"Total Return: {total_return:.2f}% (${(final_value - initial_value):,.2f})")
    print(f"Annualized Return: {annualized_return*100:.2f}%")
    print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"Maximum Drawdown: {max_drawdown:.2f}%")
    print(f"Number of Trades: {len(portfolio_values)}")

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
    strategy_name = MovingAverageCrossover.__name__
    cerebro.addstrategy(MovingAverageCrossover)

    # Set initial capital
    cerebro.broker.setcash(100000.0)
    
    # Set commission
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission

    # Add analyzers
    cerebro.addanalyzer(PortfolioAnalyzer, _name='portfolio_analyzer')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    # Print initial portfolio value
    print(f'Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}')

    # Run the backtest
    print("Starting Backtest...")
    results = cerebro.run()
    print("Backtest Complete.")

    # Get the first strategy instance
    strat = results[0]
    
    # Print performance metrics
    print_performance_metrics(strat.analyzers.portfolio_analyzer.get_analysis(), strategy_name)
    
    # Plot portfolio performance
    plot_filename = plot_portfolio_performance(strat.analyzers.portfolio_analyzer.get_analysis(), strategy_name)
    print(f'\nPortfolio performance plot saved to: {plot_filename}')

if __name__ == '__main__':
    main()