"""Bộ lọc giảm rủi ro: tin tức mạnh, cuối tuần, giới hạn số lệnh mỗi ngày."""
import json
import os
from datetime import datetime, timedelta, timezone

import config as C

HERE = os.path.dirname(os.path.abspath(__file__))
CAL_FILE = os.path.join(os.environ.get("STATE_DIR", HERE), "lich_tin.json")
CAL_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"   # lịch Forex Factory tuần này
CCY = {"XAU": "USD"}  # vàng chịu ảnh hưởng tin USD


def _load_calendar():
    """Tải lịch tin (cache 6 giờ). Lỗi mạng -> dùng bản cũ, không có thì trả []."""
    try:
        fresh = os.path.exists(CAL_FILE) and \
            (datetime.now().timestamp() - os.path.getmtime(CAL_FILE)) < 6 * 3600
        if not fresh:
            import requests
            data = requests.get(CAL_URL, timeout=20, headers={"User-Agent": "FXBot"}).json()
            with open(CAL_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        with open(CAL_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        try:
            with open(CAL_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []


def tin_manh_gan(symbol_base, now_utc, phut=None):
    """Trả về tên tin mạnh (High) của 2 đồng tiền trong cặp nếu nằm trong ±phut phút, ngược lại None."""
    phut = phut or C.NEWS_BLOCK_MINUTES
    ccys = {CCY.get(symbol_base[:3], symbol_base[:3]), CCY.get(symbol_base[3:6], symbol_base[3:6])}
    for ev in _load_calendar():
        if ev.get("impact") != "High" or ev.get("country") not in ccys:
            continue
        try:
            t = datetime.fromisoformat(ev["date"]).astimezone(timezone.utc)
        except Exception:
            continue
        if abs((t - now_utc).total_seconds()) <= phut * 60:
            return f"{ev.get('country')} {ev.get('title')} lúc {t.astimezone(timezone(timedelta(hours=7))):%H:%M}"
    return None


def cuoi_tuan(now_utc):
    """Không vào lệnh mới từ thứ Sáu (giờ UTC trong config). None = tắt bộ lọc."""
    if C.FRIDAY_CUTOFF_UTC_HOUR is None:
        return False
    return now_utc.weekday() == 4 and now_utc.hour >= C.FRIDAY_CUTOFF_UTC_HOUR or now_utc.weekday() >= 5


def du_lenh_hom_nay(state, today_vn):
    if not C.MAX_SIGNALS_PER_DAY:          # 0 = không giới hạn
        return False
    return state.get("dem_ngay", {}).get(today_vn, 0) >= C.MAX_SIGNALS_PER_DAY
