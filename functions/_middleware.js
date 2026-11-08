// Khoá bảng điều khiển bằng mật khẩu (biến DASH_PASSWORD đặt trong Cloudflare Pages, lấy từ GitHub Secrets).
export async function onRequest(ctx) {
  const pw = ctx.env.DASH_PASSWORD;
  if (!pw) return new Response("Bảng điều khiển chưa đặt mật khẩu.", { status: 503 });
  const h = ctx.request.headers.get("Authorization") || "";
  if (h.startsWith("Basic ")) {
    try {
      const raw = new TextDecoder().decode(Uint8Array.from(atob(h.slice(6)), (c) => c.charCodeAt(0)));
      const pass = raw.slice(raw.indexOf(":") + 1);
      if (pass === pw) return ctx.next();
    } catch (e) {}
  }
  return new Response("Cần mật khẩu để xem bảng điều khiển.", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="FXBot", charset="UTF-8"', "content-type": "text/plain; charset=utf-8" },
  });
}
