"""Cấu hình FXBot chạy trên GitHub Actions (giá lấy từ Yahoo Finance, miễn phí)."""

# ---- Vốn & rủi ro ----
ACCOUNT_BALANCE = 10000     # vốn tài khoản (USD)
RISK_PERCENT = 0.5          # % vốn rủi ro mỗi lệnh (0.5% của 10.000 = 50 USD)

# ---- Quy tắc nhóm ----
# Sau 1 tín hiệu vàng (hoặc JPY), bỏ qua tín hiệu cùng nhóm trong số giờ này. 0 = báo tất cả.
GROUP_COOLDOWN_HOURS = 0     # 0 = không nghỉ theo nhóm, báo tất cả

# ---- Thông báo ----
MAC_NOTIFY = False          # chạy trên máy chủ GitHub, không có thông báo Mac
TELEGRAM = True             # token trong GitHub Secrets: TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

ATR_PERIOD = 14

# ---- Bộ lọc giảm rủi ro ----
NEWS_BLOCK_MINUTES = 60     # có tin mạnh (High) trong ±60 phút -> vẫn báo, kèm cảnh báo
FRIDAY_CUTOFF_UTC_HOUR = None  # None = vẫn báo lệnh từ tối thứ Sáu
MAX_SIGNALS_PER_DAY = 0     # 0 = không giới hạn số tín hiệu mỗi ngày

# ---- Giữ máy thức ----
KEEP_AWAKE_ON_BATTERY = False
