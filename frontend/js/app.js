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