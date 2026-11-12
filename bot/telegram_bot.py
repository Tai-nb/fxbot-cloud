"""Gửi tin nhắn Telegram. Token lấy từ biến môi trường TELEGRAM_TOKEN (GitHub Secrets) hoặc file telegram_token.txt.
Chat ID tự lấy lần đầu (anh phải nhắn cho bot 1 tin trước), lưu vào telegram_chat_id.txt.
Chạy trực tiếp file này để gửi tin thử:  python telegram_bot.py
"""
import json
import os
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(HERE, "telegram_token.txt")
CHAT_FILE = os.path.join(HERE, "telegram_chat_id.txt")


def _read(path):
    env = {TOKEN_FILE: "TELEGRAM_TOKEN", CHAT_FILE: "TELEGRAM_CHAT_ID"}.get(path)
    if env and os.environ.get(env, "").strip():          # GitHub Secrets
        return os.environ[env].strip()
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def _api(token, method, params=None):
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        import requests  # dùng chứng chỉ của certifi — giống bot cũ của anh, chạy ổn trên máy này
        return requests.post(url, data=params or {}, timeout=20).json()
    except ImportError:
        data = urllib.parse.urlencode(params or {}).encode()
        with urllib.request.urlopen(url, data=data, timeout=20) as r:
            return json.loads(r.read().decode())


def chat_id(token):
    cid = _read(CHAT_FILE)
    if cid:
        return cid
    res = _api(token, "getUpdates")
    for upd in reversed(res.get("result", [])):
        msg = upd.get("message") or upd.get("edited_message") or {}
        if msg.get("chat", {}).get("id"):
            cid = str(msg["chat"]["id"])
            if not os.environ.get("GITHUB_ACTIONS"):
                with open(CHAT_FILE, "w", encoding="utf-8") as f:
                    f.write(cid)
            return cid
    return ""


def send(text):
    """Trả về (True, '') nếu gửi được, ngược lại (False, lý do)."""
    token = _read(TOKEN_FILE)
    if not token:
        return False, "chưa có telegram_token.txt"
    try:
        cid = chat_id(token)
        if not cid:
            return False, "chưa tìm thấy chat — anh hãy mở bot trên Telegram, bấm Start và nhắn 1 tin"
        res = _api(token, "sendMessage", {"chat_id": cid, "text": text})
        return bool(res.get("ok")), "" if res.get("ok") else str(res)
    except Exception as e:  # mạng lỗi, token sai...
        return False, str(e)


def format_signal(r):
    icon = "🟢" if r["side"] == "BUY" else "🔴"
    gia = ("mua (ask)" if r["side"] == "BUY" else "bán (bid)")
    entry = f"Entry: {r['entry']}"
    if r.get("gia_luc"):
        entry += f"  (giá {gia} giao ngay lúc {r['gia_luc']})"
    ksl, ktp = r.get("khoang_sl"), r.get("khoang_tp")
    sl = f"SL: {r['sl']}" + (f"  (cách {ksl})" if ksl else "")
    tp = f"TP: {r['tp']}" + (f"  (cách {ktp}, R:R 1:{r['rr']:g})" if ktp else f"  (R:R 1:{r['rr']:g})")
    di = ""
    if r.get("gia_da_di") is not None and r.get("dong_luc"):
        di = f"Nến đóng {r['dong_luc']} · từ đó giá đã đi {r['gia_da_di']:+g} theo hướng lệnh\n"
    return (f"{icon} {r['side']} {r['symbol']} {r['tf']}\n{entry}\n{sl}\n{tp}\n"
            f"Lot: {r['lot']}  (rủi ro {r['risk_pct']}%)\n{di}"
            f"Chiến lược: {r['strategy']}\nBacktest: {r['backtest']}\n"
            f"Giờ: {r['time_vn']}\n\n"
            "⚠️ Giá trên MT5 có thể lệch vài cent so với nguồn này: vào theo giá thị trường rồi đặt SL/TP đúng KHOẢNG CÁCH ở trên. "
            "Tránh 30 phút quanh tin mạnh.\nPhân tích tham khảo, không phải lời khuyên đầu tư.")


if __name__ == "__main__":
    ok, why = send("✅ FXBot đã kết nối Telegram thành công. Khi có tín hiệu BUY/SELL, em sẽ báo anh tại đây.")
    print("Gửi thành công!" if ok else f"Chưa gửi được: {why}")
