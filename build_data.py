"""Gom trạng thái bot -> data.json cho bảng điều khiển, rồi ghi lên Cloudflare KV (nếu có khoá)."""
import json
import os
from datetime import datetime, timedelta, timezone

import cf

STATE = os.environ.get("STATE_DIR", "state")
BOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot")
VN = timezone(timedelta(hours=7))


def load(name, default):
    try:
        with open(os.path.join(STATE, name), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def lines(name, n):
    try:
        with open(os.path.join(STATE, name), encoding="utf-8") as f:
            return [l.rstrip("\n") for l in f.readlines()[-n:]]
    except Exception:
        return []


def main():
    import sys
    sys.path.insert(0, BOT)
    import config as C
    import dieu_khien as DK
    from strategies import NAMES_VI
    DK.ap_dung(C, DK.tai() if cf.creds()[0] else {})

    status = load("trang_thai_quet.json", {})
    hist = load("lich_su_quet.json", [])
    if status.get("lan_quet_cuoi") and (not hist or hist[-1].get("t") != status["lan_quet_cuoi"]):
        hist.append({"t": status["lan_quet_cuoi"], "n": status.get("tin_hieu_moi", 0), "e": len(status.get("loi", [])),
                     **({"p": 1} if status.get("tam_dung") else {})})
    hist = hist[-700:]
    with open(os.path.join(STATE, "lich_su_quet.json"), "w", encoding="utf-8") as f:
        json.dump(hist, f)

    sigs = []
    for l in lines("tin_hieu.jsonl", 200):
        try:
            sigs.append(json.loads(l))
        except Exception:
            pass
    strategies = json.load(open(os.path.join(BOT, "chien_luoc_tot_nhat.json"), encoding="utf-8"))
    data = {
        "cap_nhat": datetime.now(VN).strftime("%Y-%m-%d %H:%M"),
        "quet": status,
        "lich_su_quet": hist[-200:],
        "tin_hieu": list(reversed(sigs)),
        "nhat_ky": list(reversed(lines("nhat_ky.txt", 60))),
        "chien_luoc": [dict(ma=DK.ma_chien_luoc(s), symbol="".join(c for c in s["symbol"].upper() if c.isalpha())[:6], tf=s["tf"],
                            ten=s.get("name_vi") or NAMES_VI.get(s["strategy"], s["strategy"]), rr=s["rr"], sl_atr=s["sl_atr"],
                            thang=s.get("test_winrate"), so_lenh=s.get("test_trades"), ky_vong=s.get("test_exp_r"))
                       for s in strategies],
        "cai_dat": {"von": C.ACCOUNT_BALANCE, "rui_ro": C.RISK_PERCENT, "tin_manh_phut": C.NEWS_BLOCK_MINUTES},
    }
    text = json.dumps(data, ensure_ascii=False)
    with open(os.path.join(STATE, "data.json"), "w", encoding="utf-8") as f:
        f.write(text)
    try:
        ok = cf.kv_put("data", text)
        print("Đã cập nhật bảng điều khiển" if ok else "Chưa có khoá Cloudflare – bỏ qua cập nhật bảng")
    except Exception as e:
        print(f"Lỗi cập nhật bảng: {e}")


if __name__ == "__main__":
    main()
