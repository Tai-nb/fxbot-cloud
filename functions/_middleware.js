// Khoá bảng điều khiển bằng mật khẩu (DASH_PASSWORD trong Cloudflare Pages, lấy từ GitHub Secrets).
// Đăng nhập một lần bằng form, trình duyệt nhớ 1 năm (cookie).
const COOKIE = "fx_auth";

async function sign(pw) {
  const data = new TextEncoder().encode("fxbot:" + pw);
  const buf = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function loginPage(error) {
  const msg = error ? '<p class="err">Sai mật khẩu, anh thử lại.</p>' : "";
  return new Response(
    `<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FXBot – Đăng nhập</title><style>
:root{--bg:#f6f7f9;--panel:#fff;--fg:#14171a;--muted:#667085;--line:#e4e7ec;--accent:#2563eb;--bad:#c4320a}
@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--panel:#171a21;--fg:#e8eaed;--muted:#98a2b3;--line:#2a2f3a;--accent:#6ea8fe;--bad:#ff7a59}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;display:flex;min-height:100vh;align-items:center;justify-content:center;padding:16px;box-sizing:border-box}
form{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:22px;width:100%;max-width:340px}
h1{font-size:20px;margin:0 0 4px}p{color:var(--muted);font-size:14px;margin:0 0 14px}
input{width:100%;box-sizing:border-box;font-size:16px;padding:11px 12px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--fg)}
button{margin-top:12px;width:100%;font-size:16px;padding:11px;border:0;border-radius:8px;background:var(--accent);color:#fff;font-weight:600}
.err{color:var(--bad)}</style></head><body>
<form method="post" action="/login"><h1>FXBot – Bảng tín hiệu</h1><p>Nhập mật khẩu để xem.</p>${msg}
<input type="password" name="password" autocomplete="current-password" placeholder="Mật khẩu" autofocus required>
<button type="submit">Đăng nhập</button></form></body></html>`,
    { status: error ? 401 : 200, headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" } }
  );
}

export async function onRequest(ctx) {
  const pw = ctx.env.DASH_PASSWORD;
  if (!pw) return new Response("Bảng điều khiển chưa đặt mật khẩu.", { status: 503 });
  const url = new URL(ctx.request.url);
  const token = await sign(pw);

  if (url.pathname === "/login" && ctx.request.method === "POST") {
    const form = await ctx.request.formData();
    if (String(form.get("password") || "") === pw) {
      return new Response(null, {
        status: 303,
        headers: {
          location: "/",
          "set-cookie": `${COOKIE}=${token}; Path=/; Max-Age=31536000; HttpOnly; Secure; SameSite=Lax`,
        },
      });
    }
    return loginPage(true);
  }
  if (url.pathname === "/logout") {
    return new Response(null, { status: 303, headers: { location: "/", "set-cookie": `${COOKIE}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax` } });
  }

  const cookie = ctx.request.headers.get("cookie") || "";
  const ok = cookie.split(/;\s*/).some((c) => c === `${COOKIE}=${token}`);
  if (ok) return ctx.next();
  if (url.pathname.startsWith("/api/")) {
    return new Response(JSON.stringify({ error: "Cần đăng nhập" }), { status: 401, headers: { "content-type": "application/json; charset=utf-8" } });
  }
  return loginPage(false);
}
