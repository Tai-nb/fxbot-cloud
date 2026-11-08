"""FXBot trên MacBook – quét 7 chiến lược mỗi 15 phút (launchd), báo Telegram + thông báo Mac.
Chạy thử:  python3 scanner.py --test
Không tự đặt lệnh."""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
import config as C
import data_yahoo as D
import bo_loc_rui_ro as R
from indicators import atr
from strategies import signals

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.environ.get("STATE_DIR", HERE)          # trạng thái lưu ngoài thư mục code (GitHub Actions)
os.makedirs(STATE, exist_ok=True)
P = lambda f: os.path.join(STATE, f)
VN = timezone(timedelta(hours=7))


def now_vn():
    return datetime.now(VN)


def log(msg):
    with open(P("nhat_ky.txt"), "a", encoding="utf-8") as f:
        f.write(f"{now_vn():%Y-%m-%d %H:%M} {msg}\n")


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def group_of(symbol):
    s = D.base(symbol)
    if s.startswith("XAU"):
        return "VANG"
    if "JPY" in s:
        return "JPY"
    return None


def usd_per_point_per_lot(symbol, price_cache):
    """Giá trị (USD) khi giá chạy 1.0 đơn vị, với 1 lot chuẩn."""
    b = D.base(symbol)
    if b.startswith("XAU"):
        return 100.0
    quote = b[3:]
    if quote == "USD":
        return 100000.0
    if quote in ("AUD", "NZD", "GBP", "EUR"):          # ví dụ EURAUD: 1 lot = 100.000 AUD
        pair = quote + "USD"
        if pair not in price_cache:
            df = D.rates(pair, "H1")
            price_cache[pair] = float(df["close"].iloc[-1]) if df is not None else None
        r = price_cache[pair]
        return 100000.0 * r if r else None
    conv = {"JPY": "USDJPY", "CHF": "USDCHF", "CAD": "USDCAD"}.get(quote)
    if conv:
        if conv not in price_cache:
            df = D.rates(conv, "H1")
            price_cache[conv] = float(df["close"].iloc[-1]) if df is not None else None
        r = price_cache[conv]
        return 100000.0 / r if r else None
    return None


def notify_mac(title, text):
    if not C.MAC_NOTIFY or sys.platform != "darwin":
        return
    t = title.replace('"', "'")
    x = text.replace('"', "'")
    subprocess.run(["osascript", "-e", f'display notification "{x}" with title "{t}" sound name "Glass"'],
                   check=False)


def send_telegram(text):
    if not C.TELEGRAM:
        return
    try:
        import telegram_bot as TG
        ok, why = TG.send(text)
        if not ok:
            log(f"Telegram lỗi: {why}")
    except Exception as e:
        log(f"Telegram lỗi: {e}")


def giu_may_thuc():
    """Giữ Mac thức tới lượt quét sau (kể cả khi dùng pin). Màn hình vẫn tắt bình thường.
    Mỗi lượt quét gia hạn thêm ~17 phút, nên máy thức liên tục khi bot đang chạy."""
    if getattr(C, "KEEP_AWAKE_ON_BATTERY", False) and sys.platform == "darwin":
        try:
            subprocess.Popen(["/usr/bin/caffeinate", "-i", "-t", "1020"], start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            log(f"Không bật được chế độ giữ máy thức: {e}")


def scan():
    giu_may_thuc()
    strategies = load(os.path.join(HERE, "chien_luoc_tot_nhat.json"), [])
    sent = load(P("da_gui.json"), {})
    state = load(P("trang_thai.json"), {"group_last": {}})
    price_cache, new, errors = {}, [], []
    cache = {}
    for s in strategies:
        key_df = (D.base(s["symbol"]), s["tf"])
        try:
            if key_df not in cache:
                cache[key_df] = D.rates(s["symbol"], s["tf"])
            df = cache[key_df]
        except Exception as e:
            errors.append(f"{s['symbol']} {s['tf']}: {e}")
            continue
        if df is None or len(df) < 300:
            errors.append(f"{s['symbol']} {s['tf']}: thiếu dữ liệu")
            continue
        closed = df.iloc[:-1]
        side = int(signals(s["strategy"], closed, s["params"]).iloc[-1])
        bar_time = str(closed.index[-1])
        key = f"{s['symbol']}|{s['tf']}|{s['strategy']}|{bar_time}"
        if side == 0 or key in sent:
            continue
        sent[key] = now_vn().strftime("%Y-%m-%d %H:%M")
        # ---- Bộ lọc giảm rủi ro ----
        now_utc = datetime.now(timezone.utc)
        ten = f"{D.base(s['symbol'])} {s['tf']} ({'BUY' if side == 1 else 'SELL'})"
        if R.cuoi_tuan(now_utc):
            log(f"Bỏ qua {ten} – sát cuối tuần, tránh khoảng trống giá")
            continue
        tin = R.tin_manh_gan(D.base(s["symbol"]), now_utc)
        canh_bao_tin = ""
        if tin:                                   # vẫn báo, kèm cảnh báo để anh tự cân nhắc
            log(f"Có tin mạnh gần {ten}: {tin} – vẫn báo kèm cảnh báo")
            canh_bao_tin = f"\n⚠️ CÓ TIN MẠNH: {tin}. Giá có thể giật mạnh – anh cân nhắc kỹ trước khi vào."
        today = now_vn().strftime("%Y-%m-%d")
        if R.du_lenh_hom_nay(state, today):
            log(f"Bỏ qua {ten} – đã đủ {C.MAX_SIGNALS_PER_DAY} tín hiệu hôm nay")
            continue
        g = group_of(s["symbol"])
        if g:
            last = state["group_last"].get(g)
            if last and now_vn() - datetime.fromisoformat(last) < timedelta(hours=C.GROUP_COOLDOWN_HOURS):
                log(f"Bỏ qua {s['symbol']} {s['tf']} – nhóm {g} vừa có tín hiệu lúc {last[:16]}")
                continue
            state["group_last"][g] = now_vn().isoformat()
        dem = state.setdefault("dem_ngay", {})
        dem[today] = dem.get(today, 0) + 1
        state["dem_ngay"] = dict(list(dem.items())[-14:])
        a = float(atr(closed, C.ATR_PERIOD).iloc[-1])
        d = s["sl_atr"] * a
        entry = float(df["close"].iloc[-1])
        sl = entry - d if side == 1 else entry + d
        tp = entry + s["rr"] * d if side == 1 else entry - s["rr"] * d
        dg = 2 if D.base(s["symbol"]).startswith("XAU") else (3 if "JPY" in D.base(s["symbol"]) else 5)
        lot, risk_usd, canh_bao = None, None, ""
        if C.ACCOUNT_BALANCE:
            risk_usd = C.ACCOUNT_BALANCE * C.RISK_PERCENT / 100
            v = usd_per_point_per_lot(s["symbol"], price_cache)
            if v:
                lot = max(0.01, round(risk_usd / (d * v), 2))
                that = lot * d * v                       # rủi ro thực tế với lot đã làm tròn
                canh_bao = "" if that <= risk_usd * 1.3 else (
                    f"  ⚠️ VƯỢT MỨC: lot nhỏ nhất đã mất ~{that:.0f} USD (> {risk_usd:.0f}). "
                    f"Nên BỎ QUA lệnh này nếu anh muốn giữ đúng mức rủi ro.")
                risk_usd = that
        rec = dict(time_vn=now_vn().strftime("%Y-%m-%d %H:%M"), symbol=D.base(s["symbol"]), tf=s["tf"],
                   side="BUY" if side == 1 else "SELL", entry=round(entry, dg), sl=round(sl, dg),
                   tp=round(tp, dg), rr=s["rr"], lot=(f"{lot}  (mất ~{risk_usd:.0f} USD nếu chạm SL){canh_bao}" if lot else "chưa có vốn – xem config.py"),
                   risk_pct=C.RISK_PERCENT, strategy=s["name_vi"], bar_close=bar_time,
                   nguon=D.used_ticker(s["symbol"]),
                   backtest=f"thắng {s['test_winrate']}% / {s['test_trades']} lệnh test, kỳ vọng {s['test_exp_r']:+}R",
                   canh_bao_tin=canh_bao_tin)
        new.append(rec)

    for r in new:
        with open(P("tin_hieu.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        try:
            import telegram_bot as TG
            msg = TG.format_signal(r)
        except Exception:
            msg = json.dumps(r, ensure_ascii=False)
        if r.get("canh_bao_tin"):
            msg += r["canh_bao_tin"]
        if r["nguon"] == "GC=F":
            msg += "\n(Vàng theo giá hợp đồng tương lai GC=F, thường cao hơn giá sàn vài giá – chỉnh entry/SL/TP theo chênh lệch.)"
        send_telegram(msg)
        notify_mac(f"{r['side']} {r['symbol']} {r['tf']}", f"Entry {r['entry']} SL {r['sl']} TP {r['tp']}")

    # Theo dõi mất kết nối: tất cả cặp đều lỗi dữ liệu = mất mạng / Yahoo lỗi
    if strategies and len(errors) >= len(strategies):
        state.setdefault("mat_ket_noi_tu", now_vn().strftime("%Y-%m-%d %H:%M"))
    elif state.get("mat_ket_noi_tu"):
        tu = state.pop("mat_ket_noi_tu")
        phut = (now_vn() - datetime.strptime(tu, "%Y-%m-%d %H:%M").replace(tzinfo=VN)).total_seconds() / 60
        if phut >= 30:
            send_telegram(f"⚠️ Bot đã mất kết nối dữ liệu từ {tu[11:]} đến {now_vn():%H:%M} "
                          f"(khoảng {phut:.0f} phút) – có thể đã bỏ lỡ tín hiệu trong khoảng này. Giờ đã chạy lại bình thường.")
    save(P("da_gui.json"), dict(list(sent.items())[-3000:]))
    save(P("trang_thai.json"), state)
    status = dict(lan_quet_cuoi=now_vn().strftime("%Y-%m-%d %H:%M"), tin_hieu_moi=len(new), loi=errors)
    save(P("trang_thai_quet.json"), status)
    if errors:
        log("Lỗi dữ liệu: " + "; ".join(errors))
    print(f"Quét xong: {len(new)} tín hiệu mới, {len(errors)} lỗi dữ liệu")
    return new


def test():
    print("Kiểm tra dữ liệu Yahoo cho 7 chiến lược...")
    lines = []
    for s in load(os.path.join(HERE, "chien_luoc_tot_nhat.json"), []):
        df = D.rates(s["symbol"], s["tf"])
        if df is None:
            lines.append(f"❌ {D.base(s['symbol'])} {s['tf']}: không lấy được dữ liệu")
        else:
            lines.append(f"✅ {D.base(s['symbol'])} {s['tf']}: {len(df)} nến, nến cuối {df.index[-1]:%d/%m %H:%M} UTC, "
                         f"giá {df['close'].iloc[-1]:.5g} ({D.used_ticker(s['symbol'])})")
    print("\n".join(lines))
    send_telegram("✅ FXBot trên MacBook đã chạy.\n" + "\n".join(lines))
    notify_mac("FXBot", "Đã cài xong trên MacBook – Telegram đã gửi tin thử")


if __name__ == "__main__":
    test() if "--test" in sys.argv else scan()
