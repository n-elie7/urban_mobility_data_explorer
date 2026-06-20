
// Leaflet choropleth. Zones come from PostGIS as GeoJSON; values are joined
// client-side by location_id and the fill is scaled to the selected metric.
let map, zoneLayer;

function initMap() {
  map = L.map("map").setView([40.73, -73.94], 10);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap, © CARTO", maxZoom: 18,
  }).addTo(map);
}

function colorFor(v, max) {
  if (v == null || !max) return "#2a303b";
  const t = Math.min(v / max, 1);
  const l = 25 + t * 45;

  return `hsl(48 90% ${l}%)`;
}

async function renderChoropleth(metric, valuesById) {
  const geoJson = await API.geojson();
  const max = Math.max(...Object.values(valuesById), 1);

  if (zoneLayer) map.removeLayer(zoneLayer);
  zoneLayer = L.geoJSON(geoJson, {
    style: (f) => ({
      weight: 0.5, color: "#000", fillOpacity: 0.75,
      fillColor: colorFor(valuesById[f.properties.location_id], max),
    }),
    
    onEachFeature: (f, layer) => {
      const v = valuesById[f.properties.location_id];
      layer.bindPopup(`<b>${f.properties.zone}</b><br>${f.properties.borough}<br>${metric}: ${v ?? "—"}`);
    },
  }).addTo(map);
}
