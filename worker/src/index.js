// Legion TD 2 API 代理：官方規定 key 不能放前端，所以 key 存在 Worker secret（LTD2_API_KEY），
// 前端只呼叫這裡。只開放 games/byId，只回應 ALLOWED_ORIGINS 裡的網頁。
const API = "https://apiv2.legiontd2.com/games/byId/";
const MATCH_ID = /^[0-9a-f]{64}$/;

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    if (!env.ALLOWED_ORIGINS.split(",").includes(origin)) {
      return json({ error: "origin not allowed" }, 403, {});
    }
    const cors = { "Access-Control-Allow-Origin": origin, "Vary": "Origin" };
    if (request.method !== "GET") return json({ error: "method not allowed" }, 405, cors);

    const m = new URL(request.url).pathname.match(/^\/match\/([^/]+)$/);
    if (!m || !MATCH_ID.test(m[1])) return json({ error: "bad match id" }, 400, cors);

    const res = await fetch(`${API}${m[1]}?includeDetails=true`, {
      headers: { "x-api-key": env.LTD2_API_KEY },
    });
    const headers = { ...cors, "Content-Type": "application/json" };
    // 打完的對局不會再變；workers.dev 沒有伺服器端快取，交給瀏覽器快取
    if (res.ok) headers["Cache-Control"] = "public, max-age=31536000, immutable";
    return new Response(res.body, { status: res.status, headers });
  },
};

function json(obj, status, headers) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...headers, "Content-Type": "application/json" },
  });
}
