// Trạng thái công nhân Cloudflare + các lượt chạy GitHub gần nhất (qua service binding HEN_GIO).
export async function onRequestGet({ env }) {
  if (!env.HEN_GIO) return Response.json({ loi: "Chưa nối công nhân Cloudflare (HEN_GIO)" }, { status: 503 });
  const r = await env.HEN_GIO.fetch("https://hen-gio/trang-thai");
  return new Response(r.body, { status: r.status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
}
