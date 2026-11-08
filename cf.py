"""Gọi API Cloudflare: tìm/tạo kho dữ liệu KV và ghi dữ liệu cho bảng điều khiển.
Cần biến môi trường CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID (lưu trong GitHub Secrets)."""
import os

import requests

API = "https://api.cloudflare.com/client/v4"
KV_TITLE = "fxbot-data"


def creds():
    tok, acc = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip(), os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    return (tok, acc) if tok and acc else (None, None)


def kv_namespace_id():
    tok, acc = creds()
    if not tok:
        return None
    h = {"Authorization": f"Bearer {tok}"}
    r = requests.get(f"{API}/accounts/{acc}/storage/kv/namespaces", headers=h, params={"per_page": 100}, timeout=30).json()
    if not r.get("success"):
        raise RuntimeError(f"Cloudflare từ chối liệt kê KV: {r.get('errors')}")
    for ns in r.get("result", []):
        if ns.get("title") == KV_TITLE:
            return ns["id"]
    r = requests.post(f"{API}/accounts/{acc}/storage/kv/namespaces", headers=h, json={"title": KV_TITLE}, timeout=30).json()
    if not r.get("success"):
        raise RuntimeError(f"Cloudflare từ chối tạo KV: {r.get('errors')}")
    return r["result"]["id"]


def kv_put(key, text):
    tok, acc = creds()
    if not tok:
        return False
    ns = kv_namespace_id()
    r = requests.put(f"{API}/accounts/{acc}/storage/kv/namespaces/{ns}/values/{key}",
                     headers={"Authorization": f"Bearer {tok}", "Content-Type": "text/plain; charset=utf-8"},
                     data=text.encode("utf-8"), timeout=30).json()
    if not r.get("success"):
        raise RuntimeError(f"Cloudflare từ chối ghi KV: {r.get('errors')}")
    return True


if __name__ == "__main__":
    # Dùng khi triển khai bảng: in ra wrangler.toml có id kho KV
    import sys
    project = sys.argv[1] if len(sys.argv) > 1 else "fxbot-tn"
    ns = kv_namespace_id()
    if not ns:
        sys.exit("Thiếu CLOUDFLARE_API_TOKEN / CLOUDFLARE_ACCOUNT_ID trong GitHub Secrets")
    open("wrangler.toml", "w").write(
        f'name = "{project}"\npages_build_output_dir = "site"\ncompatibility_date = "2025-06-01"\n\n'
        f'[[kv_namespaces]]\nbinding = "FXDATA"\nid = "{ns}"\n')
    print("wrangler.toml đã tạo với KV", ns[:6] + "…")
