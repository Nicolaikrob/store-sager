"""Download Yahoo Finance OHLCV and expose sliding windows as a PyTorch Dataset."""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd
import torch
import yfinance as yf
from torch import Tensor
from torch.utils.data import DataLoader, Dataset

DEFAULT_TICKERS = [
    "SPY",
    "QQQ",
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "BRK-B",
    "JPM",
    "XOM",
    "UNH",
    "COST",
]


def _per_ticker_arrays(
    raw: pd.DataFrame,
    feature_cols: tuple[str, ...],
) -> dict[str, np.ndarray]:
    """Split a yfinance frame into {symbol: (T, F) float32}, newest row last (yfinance default)."""
    out: dict[str, np.ndarray] = {}
    if raw.empty:
        return out

    if isinstance(raw.columns, pd.MultiIndex):
        for sym in raw.columns.get_level_values(0).unique():
            try:
                block = raw[sym][list(feature_cols)]
            except KeyError:
                continue
            block = block.astype(np.float64).dropna(how="any")
            if len(block) < 2:
                continue
            out[str(sym)] = block.to_numpy(dtype=np.float32, copy=True)
    else:
        block = raw[list(feature_cols)].astype(np.float64).dropna(how="any")
        if len(block) < 2:
            return out
        out["_"] = block.to_numpy(dtype=np.float32, copy=True)

    return out


class YFinanceWindowDataset(Dataset[tuple[Tensor, Tensor]]):
    """Sliding windows over daily (or other interval) bars.

    Each item is ``(x, y)`` where ``x`` has shape ``(seq_len, n_features)`` and ``y`` is shape ``(1,)``:
    by default the **next-bar log return of Close** after the window (uses closes at the last window
    bar and the following bar).
    """

    def __init__(
        self,
        tickers: list[str],
        start: str,
        end: str | None = None,
        *,
        seq_len: int = 20,
        feature_cols: tuple[str, ...] = ("Open", "High", "Low", "Close", "Volume"),
        interval: str = "1d",
        auto_adjust: bool = True,
        group_by: str = "ticker",
        progress: bool = False,
        target: Literal["next_log_return", "next_close_ratio"] = "next_log_return",
    ) -> None:
        if seq_len < 1:
            raise ValueError("seq_len must be at least 1")
        if "Close" not in feature_cols:
            raise ValueError("feature_cols must include 'Close' for the default targets")

        raw = yf.download(
            tickers,
            start=start,
            end=end,
            interval=interval,
            auto_adjust=auto_adjust,
            group_by=group_by,
            progress=progress,
        )
        self._arrays = _per_ticker_arrays(raw, feature_cols)
        self._close_col = feature_cols.index("Close")
        self._seq_len = seq_len
        self._target = target

        self._windows: list[tuple[str, int]] = []
        for sym, arr in self._arrays.items():
            n = arr.shape[0]
            # Window rows [i : i + seq_len); target uses close[i + seq_len] vs close[i + seq_len - 1]
            for start_row in range(0, max(0, n - seq_len)):
                self._windows.append((sym, start_row))

    def __len__(self) -> int:
        return len(self._windows)

    def __getitem__(self, idx: int) -> tuple[Tensor, Tensor]:
        sym, start_row = self._windows[idx]
        arr = self._arrays[sym]
        window = arr[start_row : start_row + self._seq_len]
        close_last = float(window[-1, self._close_col])
        close_next = float(arr[start_row + self._seq_len, self._close_col])

        x = torch.from_numpy(window.copy())
        denom = max(close_last, 1e-12)
        if self._target == "next_log_return":
            y = torch.tensor([np.log(close_next / denom)], dtype=torch.float32)
        else:
            y = torch.tensor([close_next / denom], dtype=torch.float32)
        return x, y


def build_default_loader(
    *,
    batch_size: int = 32,
    seq_len: int = 20,
    start: str = "2015-01-01",
    shuffle: bool = True,
) -> DataLoader[tuple[Tensor, Tensor]]:
    """Convenience: ``DataLoader`` over :class:`YFinanceWindowDataset` with :data:`DEFAULT_TICKERS`."""
    ds = YFinanceWindowDataset(DEFAULT_TICKERS, start=start, seq_len=seq_len)
    return DataLoader(ds, batch_size=batch_size, shuffle=shuffle)


if __name__ == "__main__":
    ds = YFinanceWindowDataset(DEFAULT_TICKERS[:3], start="2020-01-01", seq_len=10)
    loader = DataLoader(ds, batch_size=8, shuffle=True)
    xb, yb = next(iter(loader))
    print("batch x:", xb.shape, "dtype", xb.dtype)
    print("batch y:", yb.shape, "dtype", yb.dtype)
