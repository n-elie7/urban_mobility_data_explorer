let hourlyChart, zoneChart;

function drawHourly(rows, metric, metricLabel) {
  const context = document.getElementById("hourlyChart");
  const labels = rows.map((row) => row.pickup_hour);
  const data = rows.map((row) => row[metric]);

  hourlyChart?.destroy();
  hourlyChart = new Chart(context, {
    type: "bar",
    data: { labels, datasets: [{ label: metricLabel, data, backgroundColor: "#f5c518" }] },
    options: { plugins: { legend: { display: false } }, scales: { x: { title: { display: true, text: "Hour" } } } },
  });
}

function drawTopZones(rows, metric, metricLabel) {
  const sorted = [...rows].sort((first, second) => (second[metric] ?? 0) - (first[metric] ?? 0));
  const top = sorted.slice(0, 10);
  const context = document.getElementById("zoneChart");

  zoneChart?.destroy();
  zoneChart = new Chart(context, {
    type: "bar",
    data: {
      labels: top.map((row) => row.zone ?? row.location_id),
      datasets: [{ label: metricLabel, data: top.map((row) => row[metric]), backgroundColor: "#5ab1ef" }],
    },
    options: { indexAxis: "y", plugins: { legend: { display: false } } },
  });
}