"""Giá giao ngay theo thời gian thực để báo Entry sát giá sàn (Exness).

Nến để phát hiện tín hiệu vẫn lấy từ Yahoo (vàng theo GC=F – hợp đồng tương lai, trễ ~10 phút).
Còn Entry/SL/TP trong tin nhắn lấy theo giá giao ngay ngay lúc gửi:
  1) Swissquote (giá bid/ask giao ngay, cập nhật liên tục, miễn phí)
  2) gold-api.com (chỉ vàng, giá giữa)
Không lấy được thì trả None và bot dùng giá Yahoo như cũ (tin nhắn sẽ ghi rõ).
"""
import statistics
from datetime import datetime, timezone

import requests

H = {"User-Agent": "fxbot/1.0"}
SQ = "https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/{}/{}"


def _swissquote(base):
    r = requests.get(SQ.format(base[:3], base[3:]), headers=H, timeout=10)
    r.raise_for_status()
    rows = []
    for p in r.json():
        for s in p.get("spreadProfilePrices", [])[:1]:
            if s.get("bid") and s.get("ask"):
                rows.append((float(s["bid"]), float(s["ask"]), p.get("ts")))
    if not rows:
        return None
    bid = statistics.median(x[0] for x in rows)
    ask = statistics.median(x[1] for x in rows)
    ts = max((x[2] for x in rows if x[2]), default=None)
    t = datetime.fromtimestamp(ts / 1000, timezone.utc) if ts else datetime.now(timezone.utc)
    return dict(bid=bid, ask=ask, luc=t, nguon="Swissquote")


def _gold_api():
    j = requests.get("https://api.gold-api.com/price/XAU", headers=H, timeout=10).json()
    p = float(j["price"])
    return dict(bid=p, ask=p, luc=datetime.now(timezone.utc), nguon="gold-api.com")


def lay(base):
    """{'bid','ask','luc' (UTC),'nguon'} hoặc None."""
    try:
        q = _swissquote(base)
        if q and q["ask"] >= q["bid"] > 0:
            return q
    except Exception:
        pass
    if base == "XAUUSD":
        try:
            return _gold_api()
        except Exception:
            pass
    return None


# ---- Chênh lệch giá tương lai GC=F so với giá giao ngay (để ước tính giá giao ngay lúc nến đóng) ----
def ghi_mau_vang(state, q):
    """Lưu giá giao ngay mỗi lượt quét; lượt sau so với nến 1 phút GC=F cùng thời điểm."""
    if not q:
        return
    m = state.setdefault("mau_vang", [])
    m.append([q["luc"].isoformat(), (q["bid"] + q["ask"]) / 2])
    state["mau_vang"] = m[-40:]


def chenh_lech_vang(state, gc_1m):
    """Trung vị (GC=F − giá giao ngay) từ các mẫu đã lưu nằm trong dữ liệu 1 phút GC=F. None nếu chưa đủ."""
    if gc_1m is None or gc_1m.empty:
        return None
    import pandas as pd
    idx = gc_1m.index
    diffs = []
    for t, mid in state.get("mau_vang", []):
        ts = pd.Timestamp(t).tz_convert("UTC").tz_localize(None)
        if idx[0] <= ts <= idx[-1]:
            gc = float(gc_1m["close"].asof(ts))
            diffs.append(gc - mid)
    return statistics.median(diffs[-15:]) if diffs else None
