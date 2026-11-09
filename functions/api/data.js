// Dữ liệu cho bảng: trạng thái bot (do GitHub ghi) + cài đặt điều khiển + nhịp đồng hồ Cloudflare.
export async function onRequestGet({ env }) {
  const [data, dk, hg] = await Promise.all([env.FXDATA.get("data"), env.FXDATA.get("dieu_khien"), env.FXDATA.get("hen_gio")]);
  const d = data ? JSON.parse(data) : {};
  d.dieu_khien = dk ? JSON.parse(dk) : {};
  d.hen_gio = hg ? JSON.parse(hg) : null;
  return new Response(JSON.stringify(d), {
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}
