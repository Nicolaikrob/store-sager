"""Dataset utilities built on market data."""

from .first_yfinance import (
    DEFAULT_TICKERS,
    YFinanceWindowDataset,
    build_default_loader,
)

__all__ = [
    "DEFAULT_TICKERS",
    "YFinanceWindowDataset",
    "build_default_loader",
]
