// Lệnh điều khiển từ bảng (đã qua kiểm tra mật khẩu ở _middleware.js).
// { lenh: "quet_ngay" | "thu_telegram" | "luu", ... }
const json = (o, status = 200) => Response.json(o, { status, headers: { "cache-control": "no-store" } });

export async function onRequestPost({ request, env }) {
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ ok: false, loi: "Dữ liệu không hợp lệ" }, 400);
  }
  const lenh = body.lenh;
  if (lenh === "quet_ngay" || lenh === "thu_telegram") {
    if (!env.HEN_GIO) return json({ ok: false, loi: "Chưa nối công nhân Cloudflare" }, 503);
    const r = await env.HEN_GIO.fetch(`https://hen-gio/${lenh === "quet_ngay" ? "quet-ngay" : "thu-telegram"}`, { method: "POST" });
    return json(await r.json(), r.status);
  }
  if (lenh === "luu") {
    const cu = JSON.parse((await env.FXDATA.get("dieu_khien")) || "{}");
    const moi = { ...cu };
    if ("tam_dung" in body) moi.tam_dung = !!body.tam_dung;
    if ("telegram" in body) moi.telegram = !!body.telegram;
    if ("rui_ro" in body) {
      const v = Number(body.rui_ro);
      if (!(v >= 0.05 && v <= 2)) return json({ ok: false, loi: "Rủi ro phải từ 0,05% đến 2%" }, 400);
      moi.rui_ro = Math.round(v * 100) / 100;
    }
    if ("von" in body) {
      const v = Number(body.von);
      if (!(v >= 100 && v <= 1e8)) return json({ ok: false, loi: "Vốn phải từ 100 đến 100.000.000 USD" }, 400);
      moi.von = Math.round(v);
    }
    if ("tat" in body) {
      if (!Array.isArray(body.tat) || body.tat.length > 100) return json({ ok: false, loi: "Danh sách chiến lược không hợp lệ" }, 400);
      moi.tat = body.tat.filter((x) => typeof x === "string" && /^[A-Z]{6}\|(M15|H1|H4|D1)\|[a-z_]{2,30}$/.test(x));
    }
    moi.sua_luc = new Date().toISOString();
    await env.FXDATA.put("dieu_khien", JSON.stringify(moi));
    return json({ ok: true, dieu_khien: moi });
  }
  return json({ ok: false, loi: "Lệnh không hợp lệ" }, 400);
}
