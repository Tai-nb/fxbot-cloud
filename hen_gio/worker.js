// Đồng hồ Cloudflare: mỗi 15 phút (phút 1, 16, 31, 46) gọi GitHub chạy workflow "Quét tín hiệu".
// Lịch tự chạy của GitHub hay trễ/bỏ lượt, còn Cron Trigger của Cloudflare chạy đúng giờ.
// Cần secret GH_TOKEN: token GitHub (fine-grained) chỉ có quyền Actions: Read and write trên kho fxbot-cloud.
const REPO = "Tai-nb/fxbot-cloud";
const WORKFLOW = "scan.yml";

async function goiQuet(env, nguon) {
  const luc = new Date().toISOString();
  let ket_qua;
  if (!env.GH_TOKEN) {
    ket_qua = { luc, nguon, ok: false, loi: "Chưa có secret GH_TOKEN" };
  } else {
    const r = await fetch(`https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.GH_TOKEN}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "fxbot-hen-gio",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ ref: "main" }),
    });
    ket_qua = { luc, nguon, ok: r.status === 204, http: r.status, loi: r.status === 204 ? "" : (await r.text()).slice(0, 300) };
  }
  if (env.FXDATA) await env.FXDATA.put("hen_gio", JSON.stringify(ket_qua));
  return ket_qua;
}

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(goiQuet(env, "cron " + event.cron));
  },
  // Xem trạng thái lần gọi gần nhất (không lộ token).
  async fetch(request, env) {
    const s = env.FXDATA ? await env.FXDATA.get("hen_gio") : null;
    return new Response(s || '{"luc":null,"ghi_chu":"chưa chạy lần nào"}', {
      headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
    });
  },
};
