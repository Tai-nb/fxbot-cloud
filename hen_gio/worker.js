// Công nhân Cloudflare "fxbot-hen-gio"
// 1) Đồng hồ: phút 1, 11, 16, 26, 31, 41, 46, 56 mỗi giờ (cặp tiền :x1/:x6, vàng chờ thêm 10 phút vì giá Yahoo trễ) gọi GitHub chạy workflow "Quét tín hiệu" (trừ khi anh tạm dừng bot).
// 2) Nhận lệnh từ bảng điều khiển (chỉ qua service binding của Pages, đã tắt địa chỉ workers.dev):
//    POST /quet-ngay, POST /thu-telegram, GET /trang-thai
// Cần secret GH_TOKEN: token GitHub fine-grained, chỉ quyền Actions: Read and write trên kho fxbot-cloud.
const REPO = "Tai-nb/fxbot-cloud";
const GH = "https://api.github.com";

function gh(env, path, init = {}) {
  return fetch(GH + path, {
    ...init,
    headers: {
      Authorization: `Bearer ${env.GH_TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "fxbot-hen-gio",
      "Content-Type": "application/json",
    },
  });
}

async function dieuKhien(env) {
  try {
    return JSON.parse((await env.FXDATA.get("dieu_khien")) || "{}");
  } catch {
    return {};
  }
}

async function chayWorkflow(env, file) {
  if (!env.GH_TOKEN) return { ok: false, loi: "Chưa có secret GH_TOKEN trong công nhân Cloudflare" };
  const r = await gh(env, `/repos/${REPO}/actions/workflows/${file}/dispatches`, {
    method: "POST",
    body: JSON.stringify({ ref: "main" }),
  });
  return r.status === 204 ? { ok: true } : { ok: false, http: r.status, loi: (await r.text()).slice(0, 300) };
}

async function ghiHenGio(env, obj) {
  const luc = new Date().toISOString();
  const rec = { luc, ...obj };
  await env.FXDATA.put("hen_gio", JSON.stringify(rec));
  return rec;
}

async function nhipDongHo(env, cron) {
  const dk = await dieuKhien(env);
  if (dk.tam_dung) return ghiHenGio(env, { nguon: "cron " + cron, ok: true, bo_qua: "Bot đang tạm dừng" });
  const kq = await chayWorkflow(env, "scan.yml");
  return ghiHenGio(env, { nguon: "cron " + cron, ...kq });
}

async function trangThai(env) {
  const out = { co_token: !!env.GH_TOKEN, hen_gio: null, luot_chay: [], loi: "" };
  try {
    out.hen_gio = JSON.parse((await env.FXDATA.get("hen_gio")) || "null");
  } catch {}
  if (!env.GH_TOKEN) return out;
  const r = await gh(env, `/repos/${REPO}/actions/workflows/scan.yml/runs?per_page=12`);
  if (!r.ok) {
    out.loi = `GitHub trả về ${r.status}`;
    return out;
  }
  const j = await r.json();
  out.luot_chay = (j.workflow_runs || []).map((w) => ({
    id: w.id,
    su_kien: w.event,
    trang_thai: w.status,
    ket_qua: w.conclusion,
    tao_luc: w.created_at,
    bat_dau: w.run_started_at,
    cap_nhat: w.updated_at,
  }));
  return out;
}

const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(nhipDongHo(env, event.cron));
  },
  async fetch(request, env) {
    const { pathname } = new URL(request.url);
    if (request.method === "GET" && pathname === "/trang-thai") return json(await trangThai(env));
    if (request.method === "POST" && pathname === "/quet-ngay") {
      const kq = await chayWorkflow(env, "scan.yml");
      if (kq.ok) await ghiHenGio(env, { nguon: "bấm Quét ngay", ok: true });
      return json(kq, kq.ok ? 200 : 502);
    }
    if (request.method === "POST" && pathname === "/thu-telegram") {
      const kq = await chayWorkflow(env, "check.yml");
      return json(kq, kq.ok ? 200 : 502);
    }
    return json({ loi: "Không có lệnh này" }, 404);
  },
};
