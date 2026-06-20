
// all paths go through the nginx /api proxy (same origin).

const API = {
  async geojson() { return (await fetch("/api/zones/geojson")).json(); },
  async hourly(params) { return (await fetch("/api/analytics/hourly-demand?" + qs(params))).json(); },
  async byZone(params) { return (await fetch("/api/analytics/by-zone?" + qs(params))).json(); },
  async flows(top = 50) { return (await fetch(`/api/analytics/flows?top=${top}`)).json(); },
};
function qs(params = {}) {
  return Object.entries(params).filter(([, v]) => v).map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join("&");
}
