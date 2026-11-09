"""Cài đặt chỉnh từ bảng điều khiển (Cloudflare KV, khoá "dieu_khien").
Chỉ có tác dụng khi chạy trên GitHub (có khoá Cloudflare). Bot trên Mac không có khoá nên giữ nguyên config.py.

Các trường:
  tam_dung: bool          – tạm dừng quét
  telegram: bool          – gửi Telegram hay không
  rui_ro: float           – % vốn mỗi lệnh (0.05–2)
  von: float              – vốn tính lot (USD)
  tat: [ma chiến lược]    – các chiến lược đang tắt, ma = "XAUUSD|H1|rsi_pullback"
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def ma_chien_luoc(s):
    base = "".join(c for c in s["symbol"].upper() if c.isalpha())[:6]
    return f"{base}|{s['tf']}|{s['strategy']}"


def tai():
    try:
        import cf
        raw = cf.kv_get("dieu_khien")
        return json.loads(raw) if raw else {}
    except Exception as e:
        print(f"Không đọc được cài đặt từ bảng điều khiển ({e}) – dùng config.py")
        return {}


def ap_dung(C, dk):
    """Ghi đè config theo bảng điều khiển, có kiểm tra giới hạn an toàn."""
    try:
        r = float(dk.get("rui_ro", C.RISK_PERCENT))
        if 0.05 <= r <= 2:
            C.RISK_PERCENT = r
    except (TypeError, ValueError):
        pass
    try:
        v = float(dk.get("von", C.ACCOUNT_BALANCE))
        if 100 <= v <= 1e8:
            C.ACCOUNT_BALANCE = v
    except (TypeError, ValueError):
        pass
    if "telegram" in dk:
        C.TELEGRAM = bool(dk["telegram"])
