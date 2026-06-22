

// all paths go through the nginx /api proxy (same origin).

const API = {
  async geojson() { return (await fetch("/api/zones/geojson")).json(); },
  async hourly(parameters) { return (await fetch("/api/analytics/hourly-demand?" + queryString(parameters))).json(); },
  async byZone(parameters) { return (await fetch("/api/analytics/by-zone?" + queryString(parameters))).json(); },
  async flows(top = 50) { return (await fetch(`/api/analytics/flows?top=${top}`)).json(); },
  async dataRange() { return (await fetch("/api/analytics/data-range")).json(); },
};

function queryString(parameters = {}) {
  return Object.entries(parameters)
    .filter(([, value]) => value !== null && value !== undefined && value !== "")
    .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
    .join("&");
}
