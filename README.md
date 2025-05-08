# ToTheMoon

**ToTheMoon** is an evolving, modular framework for building, testing, and eventually deploying fully autonomous trading agents. Designed for flexibility and extensibility, it empowers both quants and tinkerers to experiment with classic and AI-driven trading strategies, all under a unified, robust backtesting engine.

## 🚀 Vision

ToTheMoon aims to become a fully autonomous trader capable of:
- Executing a wide range of well-tested strategies (from simple moving averages to advanced machine learning models)
- Seamlessly integrating new data sources and vendors
- Running rigorous backtests with detailed analytics and visualizations
- Eventually, discovering and optimizing new strategies autonomously ("strategy discovery")
- Plug-and-play extensibility for new models, strategies, and data feeds

## 🧠 Features

- **Backtesting Engine**: Powered by [Backtrader](https://www.backtrader.com/), with custom analyzers and performance metrics.
- **Strategy Framework**: Easily add or swap strategies. Includes a baseline Moving Average Crossover; ML-based strategies are in the works.
- **Data Abstraction Layer**: Unified interface for multiple data vendors (Yahoo Finance, Polygon, and more), with smart caching and efficient data loading.
- **Historical Data Loader**: Download, cache, and manage historical data for any supported ticker and interval.
- **Performance Analytics**: Automatic calculation and plotting of returns, Sharpe ratio, drawdown, and more.
- **Extensible Design**: Add new strategies, models, or data vendors with minimal friction.

## 🛠️ Tech Stack

- **Python 3.8+**
- [Backtrader](https://www.backtrader.com/) (backtesting engine)
- [Pandas](https://pandas.pydata.org/) & [NumPy](https://numpy.org/) (data wrangling)
- [Matplotlib](https://matplotlib.org/) (visualization)
- [yfinance](https://github.com/ranaroussi/yfinance) (Yahoo Finance data)
- [Polygon.io](https://polygon.io/) (alternative data vendor, optional)
- Modular architecture for future AI/ML integration (LSTM, custom models, etc.)

## 📈 Example: Moving Average Crossover

The example strategy implements a classic moving average crossover:
- Buys when the short-term MA crosses above the long-term MA
- Sells when the short-term MA crosses below

Backtest results are visualized and key metrics are reported automatically.

## 🧩 Extending ToTheMoon

- **Add a new strategy**: Drop a new file in `moonboy/strategies/` and register it.
- **Plug in a new data vendor**: Implement the `SecuritiesVendor` interface.
- **Experiment with ML**: Build your model in `moonboy/models/` and wire it into a strategy.

## 🌌 The Future: Autonomous Strategy Discovery

The long-term vision is to enable "discoverable" strategies—where the agent can autonomously search, test, and optimize new trading strategies using AI and meta-learning. Conceptually, this would mimic a trader that not only executes but also invents and refines its own edge.

## 📂 Project Structure

```
moonboy/
  ├── backtesting/         # Backtest engine and scripts
  ├── config/              # Config files
  ├── data/                # Data loaders, vendors, and cache
  ├── models/              # ML and custom models (WIP)
  ├── strategies/          # Trading strategies (classic & ML)
  ├── test/                # Unit tests
  └── utils/               # Utilities (feature engineering, metrics, etc.)
```

## 🏁 Getting Started

1. Clone the repo
2. Install dependencies:  
   `pip install -r moonboy/requirements.txt`
3. Run a backtest:  
   `python moonboy/backtesting/run_backtest.py`
4. Check out the generated performance plots and metrics!

## 📜 License

See `LICENSE` for details.
