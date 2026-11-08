"""Lấy nến từ Yahoo Finance (miễn phí, không cần tài khoản).
Lưu ý: Yahoo không có giá vàng giao ngay ổn định -> thử XAUUSD=X trước, không có thì dùng
hợp đồng tương lai GC=F (thường cao hơn giá sàn vài giá)."""
import pandas as pd
import yfinance as yf

TICKERS = {
    "EURUSD": ["EURUSD=X"], "GBPUSD": ["GBPUSD=X"], "USDJPY": ["USDJPY=X"],
    "USDCHF": ["USDCHF=X"], "GBPCHF": ["GBPCHF=X"], "CADJPY": ["CADJPY=X"],
    "EURJPY": ["EURJPY=X"], "XAUUSD": ["GC=F"],
}
_used = {}


def base(symbol):
    """'XAUUSDm' -> 'XAUUSD' (bỏ hậu tố của sàn)."""
    return "".join(c for c in symbol.upper() if c.isalpha())[:6]


def _download(ticker, interval, period, tries=3, wait=20):
    """Tải nến, thử lại tối đa 3 lần (mạng có thể chưa sẵn sàng ngay sau khi Mac thức dậy)."""
    import time
    df = None
    for i in range(tries):
        try:
            df = yf.download(ticker, interval=interval, period=period, progress=False,
                             auto_adjust=False, threads=False)
        except Exception:
            df = None
        if df is not None and not df.empty:
            break
        if i < tries - 1:
            time.sleep(wait)
    if df is None or df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)[["open", "high", "low", "close"]].dropna()
    idx = df.index
    df.index = (idx.tz_convert("UTC") if idx.tz is not None else idx.tz_localize("UTC")).tz_localize(None)
    return df


def rates(symbol, tf):
    """Trả về DataFrame open/high/low/close, cột time theo UTC. Nến cuối có thể đang chạy."""
    b = base(symbol)
    for t in TICKERS.get(b, [b + "=X"]):
        if tf == "M15":
            df = _download(t, "15m", "30d")
        elif tf == "H1":
            df = _download(t, "60m", "120d")
        elif tf == "H4":
            h = _download(t, "60m", "300d")
            df = None if h is None else h.resample("4h", origin="epoch", label="left", closed="left").agg(
                {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
        else:
            raise ValueError(tf)
        if df is not None and len(df) > 250:
            _used[b] = t
            df["spread"] = 0
            return df
    return None


def last_price(symbol):
    df = _download(TICKERS.get(base(symbol), [base(symbol) + "=X"])[0], "1m", "1d")
    return None if df is None else float(df["close"].iloc[-1])


def used_ticker(symbol):
    return _used.get(base(symbol), "?")
