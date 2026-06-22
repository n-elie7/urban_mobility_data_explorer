// read filters, fetch aggregates, update map and charts.
const dashboardState = {
  hourly: [],
  zones: [],
  topZones: [],
  flows: [],
};

async function refresh() {
  const metricSelect = document.getElementById("metric");
  const metric = metricSelect.value;
  const metricLabel = metricSelect.options[metricSelect.selectedIndex].text;

  const parameters = {
    start_date: document.getElementById("start_date").value,
    end_date: document.getElementById("end_date").value,
  };

  const [hourly, zones] = await Promise.all([API.hourly(parameters), API.byZone(parameters)]);
  dashboardState.hourly = hourly;
  dashboardState.zones = zones;
  dashboardState.topZones = [...zones]
    .sort((first, second) => (second[metric] ?? 0) - (first[metric] ?? 0))
    .slice(0, 10);

  drawHourly(hourly, metric, metricLabel);
  drawTopZones(zones, metric, metricLabel);

  const valuesByLocationId = {};
  for (const zoneRow of zones) {
    valuesByLocationId[zoneRow.location_id] = zoneRow[metric];
  }
  await renderChoropleth(metric, metricLabel, valuesByLocationId);

  const showFlows = document.getElementById("show_flows").checked;
  if (showFlows) {
    dashboardState.flows = await API.flows(50);
    renderFlows(dashboardState.flows);
  } else {
    dashboardState.flows = [];
    clearFlows();
  }

  renderInsights(metric, metricLabel);
}

function renderInsights(metric, metricLabel) {
  const container = document.getElementById("insights");
  if (!container) return;
  container.innerHTML = "";

  const { hourly, zones, flows } = dashboardState;
  const cards = [];

  if (hourly.length > 0) {
    const peakHour = hourly.reduce((best, row) => (row.trips > best.trips ? row : best));
    const totalHourlyTrips = hourly.reduce((sum, row) => sum + (row.trips || 0), 0);
    const averageTripsPerHour = totalHourlyTrips / hourly.length;
    const liftPercent = Math.round((peakHour.trips / averageTripsPerHour - 1) * 100);
    cards.push({
      label: "Peak hour",
      value: `${String(peakHour.pickup_hour).padStart(2, "0")}:00`,
      caption: `${peakHour.trips.toLocaleString()} trips, ${liftPercent}% above the average hour in this window.`,
    });
  }

  if (zones.length > 0) {
    const totalZoneTrips = zones.reduce((sum, row) => sum + (row.trips || 0), 0);
    const topZone = zones.reduce((best, row) => (row.trips > best.trips ? row : best));
    const sharePercent = ((topZone.trips / totalZoneTrips) * 100).toFixed(1);
    const boroughSuffix = topZone.borough ? ` (${topZone.borough})` : "";
    cards.push({
      label: "Top pickup zone",
      value: (topZone.zone || `Zone ${topZone.location_id}`) + boroughSuffix,
      caption: `${topZone.trips.toLocaleString()} trips, ${sharePercent}% of all pickups in this window.`,
    });
  }

  if (flows.length > 0) {
    const topFlow = flows[0];
    cards.push({
      label: "Busiest corridor",
      value: `Zone ${topFlow.pu_location_id} → Zone ${topFlow.do_location_id}`,
      caption: `${topFlow.trips.toLocaleString()} trips on this single OD pair, drawn as the brightest arc on the map.`,
    });
  } else if (zones.length > 0) {
    const sortedByTrips = [...zones].sort((first, second) => (second.trips || 0) - (first.trips || 0));
    const topTenTotal = sortedByTrips.slice(0, 10).reduce((sum, row) => sum + (row.trips || 0), 0);
    const grandTotal = sortedByTrips.reduce((sum, row) => sum + (row.trips || 0), 0);
    const concentrationPercent = Math.round((topTenTotal / grandTotal) * 100);
    cards.push({
      label: "Demand concentration",
      value: `Top 10 zones`,
      caption: `account for ${concentrationPercent}% of all pickups, demand is heavily clustered. Toggle "Show top flows" for the corridor view.`,
    });
  }

  if (cards.length === 0) {
    container.innerHTML =
      `<div class="insight">` +
      `<div class="insight-label">No data</div>` +
      `<div class="insight-value">Apply a filter</div>` +
      `<div class="insight-caption">Pick a date range that overlaps the loaded months, then click Apply.</div>` +
      `</div>`;
    return;
  }

  for (const insight of cards) {
    const card = document.createElement("div");
    card.className = "insight";
    card.innerHTML =
      `<div class="insight-label">${insight.label}</div>` +
      `<div class="insight-value">${insight.value}</div>` +
      `<div class="insight-caption">${insight.caption}</div>`;
    container.appendChild(card);
  }
}

function downloadCsv(filename, rows) {
  if (!rows || rows.length === 0) return;

  const headers = Object.keys(rows[0]);
  const escape = (value) => {
    if (value === null || value === undefined) return "";
    const stringValue = String(value);
    return /[",\n]/.test(stringValue) ? `"${stringValue.replace(/"/g, '""')}"` : stringValue;
  };
  const lines = [
    headers.join(","),
    ...rows.map((row) => headers.map((header) => escape(row[header])).join(",")),
  ];

  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(objectUrl);
}

function toDateTimeLocal(date) {
  const pad = (number) => String(number).padStart(2, "0");
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}`
  );
}

function addDays(date, days) {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}

async function setupPresets() {
  const container = document.getElementById("presets");
  container.innerHTML = "";

  let range = { start: null, end: null };
  try {
    range = await API.dataRange();
  } catch (error) {
    console.warn("could not fetch data range", error);
  }

  const buttons = [];

  if (range.start && range.end) {
    const start = new Date(range.start);
    const end = new Date(range.end);
    buttons.push({ label: "Full range", from: start, to: end });
    buttons.push({ label: "First day", from: start, to: addDays(start, 1) });
    buttons.push({ label: "First week", from: start, to: addDays(start, 7) });
  }

  buttons.push({ label: "Reset", from: null, to: null });

  for (const preset of buttons) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "preset";
    button.textContent = preset.label;
    button.addEventListener("click", () => {
      const startInput = document.getElementById("start_date");
      const endInput = document.getElementById("end_date");
      startInput.value = preset.from ? toDateTimeLocal(preset.from) : "";
      endInput.value = preset.to ? toDateTimeLocal(preset.to) : "";
      refresh().catch((error) => console.error("preset refresh failed", error));
    });
    container.appendChild(button);
  }
}

function wireDownloads() {
  document.getElementById("download_hourly").addEventListener("click", (event) => {
    event.preventDefault();
    downloadCsv("hourly_demand.csv", dashboardState.hourly);
  });
  document.getElementById("download_zones").addEventListener("click", (event) => {
    event.preventDefault();
    downloadCsv("zones.csv", dashboardState.zones);
  });
  document.getElementById("download_top_zones").addEventListener("click", (event) => {
    event.preventDefault();
    downloadCsv("top_zones.csv", dashboardState.topZones);
  });
  document.getElementById("download_flows").addEventListener("click", (event) => {
    event.preventDefault();
    if (dashboardState.flows.length === 0) {
      alert("Enable 'Show top flows' and click Apply first, then re-download.");
      return;
    }
    downloadCsv("flows.csv", dashboardState.flows);
  });
}

window.addEventListener("DOMContentLoaded", () => {
  initMap();

  document.getElementById("apply").addEventListener("click", () => {
    refresh().catch((error) => console.error("apply refresh failed", error));
  });

  wireDownloads();
  setupPresets().catch((error) => console.error("preset setup failed", error));

  refresh().catch((error) =>
    console.error("initial load failed (is the API up + data loaded?)", error)
  );
});
