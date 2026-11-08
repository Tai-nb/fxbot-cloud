"""Thư viện chiến lược. Mỗi hàm trả về Series: +1 = BUY, -1 = SELL, 0 = không có tín hiệu,
tính tại lúc NẾN ĐÓNG CỬA; lệnh được vào ở giá mở của nến kế tiếp.
Lưới tham số cố ý nhỏ để hạn chế tối ưu hoá quá mức (overfitting)."""
import itertools
import numpy as np
import pandas as pd
from indicators import ema, rsi, bollinger, macd, stoch, adx


def _cross_up(a, b):
    return (a > b) & (a.shift(1) <= b.shift(1))


def _cross_down(a, b):
    return (a < b) & (a.shift(1) >= b.shift(1))


def _to_sig(buy, sell):
    s = pd.Series(0, index=buy.index, dtype=int)
    s[buy.fillna(False)] = 1
    s[sell.fillna(False)] = -1
    return s


def ema_cross(df, fast, slow):
    """Giao cắt EMA, chỉ đánh theo xu hướng EMA200."""
    c = df["close"]
    f, s, t = ema(c, fast), ema(c, slow), ema(c, 200)
    return _to_sig(_cross_up(f, s) & (c > t), _cross_down(f, s) & (c < t))


def rsi_pullback(df, level):
    """Xu hướng tăng (trên EMA200) + RSI vừa thoát vùng quá bán -> BUY; ngược lại SELL."""
    c = df["close"]
    r, t = rsi(c, 14), ema(c, 200)
    lo, hi = pd.Series(level, index=c.index), pd.Series(100 - level, index=c.index)
    return _to_sig(_cross_up(r, lo) & (c > t), _cross_down(r, hi) & (c < t))


def bb_reversion(df, k):
    """Giá đóng cửa quay lại trong dải Bollinger, thị trường đi ngang (ADX < 25)."""
    c = df["close"]
    lo, mid, up = bollinger(c, 20, k)
    side = adx(df, 14) < 25
    return _to_sig(_cross_up(c, lo) & side, _cross_down(c, up) & side)


def donchian_breakout(df, n):
    """Phá đỉnh/đáy n nến, có ADX > 20 xác nhận xu hướng."""
    hh = df["high"].rolling(n).max().shift(1)
    ll = df["low"].rolling(n).min().shift(1)
    c = df["close"]
    trend = adx(df, 14) > 20
    return _to_sig(_cross_up(c, hh) & trend, _cross_down(c, ll) & trend)


def macd_trend(df, dummy=0):
    """MACD cắt đường tín hiệu theo hướng EMA200, giao cắt xảy ra phía bên kia số 0 (hồi về)."""
    c = df["close"]
    line, sig = macd(c)
    t = ema(c, 200)
    return _to_sig(_cross_up(line, sig) & (line < 0) & (c > t),
                   _cross_down(line, sig) & (line > 0) & (c < t))


def stoch_pullback(df, level):
    """Stochastic %K cắt %D trong vùng quá bán/quá mua, theo xu hướng EMA50 > EMA200."""
    c = df["close"]
    k, d = stoch(df, 14, 3)
    up = ema(c, 50) > ema(c, 200)
    return _to_sig(_cross_up(k, d) & (k < level) & up,
                   _cross_down(k, d) & (k > 100 - level) & ~up)


STRATEGIES = {
    "ema_cross": (ema_cross, {"fast": [9, 20], "slow": [50]}),
    "rsi_pullback": (rsi_pullback, {"level": [30, 35]}),
    "bb_reversion": (bb_reversion, {"k": [2.0, 2.5]}),
    "donchian_breakout": (donchian_breakout, {"n": [20, 55]}),
    "macd_trend": (macd_trend, {"dummy": [0]}),
    "stoch_pullback": (stoch_pullback, {"level": [20, 30]}),
}

NAMES_VI = {
    "ema_cross": "Giao cắt EMA theo xu hướng",
    "rsi_pullback": "RSI hồi về theo xu hướng",
    "bb_reversion": "Bollinger đảo chiều (đi ngang)",
    "donchian_breakout": "Phá vỡ kênh Donchian",
    "macd_trend": "MACD hồi về theo xu hướng",
    "stoch_pullback": "Stochastic hồi về theo xu hướng",
}


def param_grid(name):
    _, grid = STRATEGIES[name]
    keys = list(grid)
    for vals in itertools.product(*(grid[k] for k in keys)):
        yield dict(zip(keys, vals))


def signals(name, df, params):
    fn, _ = STRATEGIES[name]
    return fn(df, **params)
