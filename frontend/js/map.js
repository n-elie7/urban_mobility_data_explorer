// Leaflet choropleth + flow arcs. Zones come from PostGIS as GeoJSON;
// values are joined client-side by location_id and the fill is scaled
// to the selected metric. Flow arcs come pre-enriched with centroids.
let map, zoneLayer, flowLayer, legendControl;

function initMap() {
  map = L.map("map").setView([40.73, -73.94], 10);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap, © CARTO", maxZoom: 18,
  }).addTo(map);
}

function colorFor(value, maximum) {
  if (value == null || !maximum) return "#2a303b";
  const ratio = Math.min(value / maximum, 1);
  const lightness = 25 + ratio * 45;

  return `hsl(48 90% ${lightness}%)`;
}

function formatValue(metric, value) {
  if (value == null || Number.isNaN(value)) return "—";
  if (metric === "trips") return Math.round(value).toLocaleString();
  if (metric === "average_fare") return `$${value.toFixed(2)}`;
  if (metric === "average_tip_percent") return `${value.toFixed(1)}%`;
  return value.toFixed(2);
}

function renderLegend(metric, metricLabel, maximum) {
  if (legendControl) {
    map.removeControl(legendControl);
    legendControl = null;
  }

  legendControl = L.control({ position: "bottomright" });
  legendControl.onAdd = () => {
    const container = L.DomUtil.create("div", "legend");
    const stopsCount = 5;
    const rows = [`<div class="legend-title">${metricLabel}</div>`];

    for (let stopIndex = stopsCount - 1; stopIndex >= 0; stopIndex--) {
      const lower = (maximum * stopIndex) / stopsCount;
      const upper = (maximum * (stopIndex + 1)) / stopsCount;
      const swatchColor = colorFor((lower + upper) / 2, maximum);
      rows.push(
        `<div class="legend-row">` +
        `<span class="legend-swatch" style="background:${swatchColor}"></span>` +
        `<span class="legend-label">${formatValue(metric, lower)} – ${formatValue(metric, upper)}</span>` +
        `</div>`
      );
    }

    rows.push(
      `<div class="legend-row">` +
      `<span class="legend-swatch" style="background:#2a303b"></span>` +
      `<span class="legend-label">No data</span>` +
      `</div>`
    );

    container.innerHTML = rows.join("");
    return container;
  };

  legendControl.addTo(map);
}

async function renderChoropleth(metric, metricLabel, valuesByLocationId) {
  const geoJson = await API.geojson();
  const numericValues = Object.values(valuesByLocationId).filter((value) => value != null);
  const maximum = numericValues.length ? Math.max(...numericValues) : 1;

  if (zoneLayer) map.removeLayer(zoneLayer);
  zoneLayer = L.geoJSON(geoJson, {
    style: (feature) => ({
      weight: 0.5, color: "#000", fillOpacity: 0.75,
      fillColor: colorFor(valuesByLocationId[feature.properties.location_id], maximum),
    }),

    onEachFeature: (feature, layer) => {
      const value = valuesByLocationId[feature.properties.location_id];
      layer.bindPopup(
        `<b>${feature.properties.zone}</b><br>` +
        `${feature.properties.borough}<br>` +
        `${metricLabel}: ${formatValue(metric, value)}`
      );
    },
  }).addTo(map);

  renderLegend(metric, metricLabel, maximum);
}

function quadraticBezierPoints(start, end, samples = 40) {
  const midpoint = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2];
  const deltaLat = end[0] - start[0];
  const deltaLng = end[1] - start[1];
  const distance = Math.sqrt(deltaLat * deltaLat + deltaLng * deltaLng) || 1e-9;
  const offsetMagnitude = distance * 0.18;
  const perpendicular = [-deltaLng / distance, deltaLat / distance];
  const control = [
    midpoint[0] + perpendicular[0] * offsetMagnitude,
    midpoint[1] + perpendicular[1] * offsetMagnitude,
  ];

  const points = [];
  for (let step = 0; step <= samples; step++) {
    const ratio = step / samples;
    const inverseRatio = 1 - ratio;
    const latitude =
      inverseRatio * inverseRatio * start[0] +
      2 * inverseRatio * ratio * control[0] +
      ratio * ratio * end[0];
    const longitude = 
      inverseRatio * inverseRatio * start[1] +
      2 * inverseRatio * ratio * control[1] +
      ratio * ratio * end[1];
    points.push([latitude, longitude]);
  }
  return points;
}

function renderFlows(flowRows) {
  clearFlows();
  if (!flowRows || flowRows.length === 0) return;

  const maxTrips = Math.max(...flowRows.map((row) => row.trips));
  const logMax = Math.log(maxTrips + 1) || 1;

  const arcs = flowRows.map((row) => {
    const start = [row.pickup_latitude, row.pickup_longitude];
    const end = [row.dropoff_latitude, row.dropoff_longitude];
    const weight = 1.5 + 4.5 * (Math.log(row.trips + 1) / logMax);
    const opacity = 0.3 + 0.55 * (row.trips / maxTrips);

    return L.polyline(quadraticBezierPoints(start, end), {
      color: "#ff7a45",
      weight,
      opacity,
      lineCap: "round",
    }).bindTooltip(`${row.trips.toLocaleString()} trips`);
  });

  flowLayer = L.layerGroup(arcs).addTo(map);
}

function clearFlows() {
  if (flowLayer) {
    map.removeLayer(flowLayer);
    flowLayer = null;
  }
}