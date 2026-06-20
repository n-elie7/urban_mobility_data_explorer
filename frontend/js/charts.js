
let hourlyChart, zoneChart;

function drawHourly(rows) {
  const ctx = document.getElementById("hourlyChart");
  const labels = rows.map((r) => r.pickup_hour);
  const data = rows.map((r) => r.trips);

  hourlyChart?.destroy();
  hourlyChart = new Chart(ctx, {
    type: "bar",
    data: { labels, datasets: [{ label: "Trips", data, backgroundColor: "#f5c518" }] },
    options: { plugins: { legend: { display: false } }, scales: { x: { title: { display: true, text: "Hour" } } } },
  });
}

function drawTopZones(rows) {
  const top = rows.slice(0, 10);
  const ctx = document.getElementById("zoneChart");
  
  zoneChart?.destroy();
  zoneChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: top.map((r) => r.zone ?? r.location_id),
      datasets: [{ label: "Trips", data: top.map((r) => r.trips), backgroundColor: "#5ab1ef" }],
    },
    options: { indexAxis: "y", plugins: { legend: { display: false } } },
  });
}
