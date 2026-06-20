

// read filters, fetch aggregates, update map and charts.
async function refresh() {
  const metric = document.getElementById("metric").value;
  const params = {
    start: document.getElementById("start").value,
    end: document.getElementById("end").value,
  };

  const [hourly, zones] = await Promise.all([API.hourly(params), API.byZone(params)]);

  drawHourly(hourly);
  drawTopZones(zones);

  const valuesById = {};

  for (const z of zones) {
    valuesById[z.location_id] = z[metric];
  }

  await renderChoropleth(metric, valuesById);
}

window.addEventListener("DOMContentLoaded", () => {
  initMap();

  document.getElementById("apply").addEventListener("click", refresh);
  
  refresh().catch((e) => console.error("initial load failed (is the API up + data loaded?)", e));
});
