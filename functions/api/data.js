export async function onRequestGet({ env }) {
  const v = env.FXDATA ? await env.FXDATA.get("data") : null;
  return new Response(v || "{}", {
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}
