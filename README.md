# FXBot Cloud

Bot quét tín hiệu forex/vàng chạy trên **GitHub Actions** mỗi 15 phút (không cần bật máy), gửi BUY/SELL kèm Entry/SL/TP/lot qua **Telegram**, và cập nhật **bảng tín hiệu** trên Cloudflare Pages (có mật khẩu).

## Cấu trúc
- `bot/` – bộ quét (giống bot trên MacBook): 10 chiến lược trong `bot/chien_luoc_tot_nhat.json`, cài đặt rủi ro trong `bot/config.py`.
- `build_data.py` – gom trạng thái bot, ghi lên Cloudflare KV cho bảng điều khiển.
- `site/`, `functions/` – bảng điều khiển (Cloudflare Pages + mật khẩu).
- `hen_gio/worker.js` – đồng hồ Cloudflare (Worker `fxbot-hen-gio`, Cron Trigger phút 1/16/31/46) gọi GitHub chạy quét đúng 15 phút. Cần secret `GH_TOKEN` trong Worker.
- `.github/workflows/scan.yml` – workflow quét (lịch GitHub chỉ còn dự phòng mỗi giờ); `deploy.yml` – triển khai bảng.
- Quét bù: nếu lượt trước bị lỡ, bot vẫn báo tín hiệu của nến đóng trong 75 phút gần nhất, kèm ghi chú "BÁO TRỄ".

## Secrets cần có (Settings → Secrets and variables → Actions)
| Tên | Nội dung |
|---|---|
| `TELEGRAM_TOKEN` | token bot Telegram |
| `TELEGRAM_CHAT_ID` | chat ID Telegram |
| `CLOUDFLARE_API_TOKEN` | token API Cloudflare (quyền: Cloudflare Pages – Edit, Workers KV Storage – Edit) |
| `CLOUDFLARE_ACCOUNT_ID` | Account ID Cloudflare |
| `DASH_PASSWORD` | mật khẩu xem bảng điều khiển |

Trạng thái bot (tín hiệu đã gửi, nhật ký) lưu trong bộ nhớ đệm của Actions, không đưa vào kho code.

Lưu ý: GitHub có thể chạy lịch trễ vài phút. Giá theo Yahoo Finance (vàng theo GC=F) – luôn kiểm tra lại trên MT5.

Phân tích tham khảo, không phải lời khuyên đầu tư.
