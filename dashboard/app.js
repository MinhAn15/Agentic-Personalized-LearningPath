async function loadData() {
  try {
    const response = await fetch("../data/analysis/all_results.json");
    const data = await response.json();

    updateMetrics(data);
    renderCharts(data);
    renderTable(data);
  } catch (error) {
    console.error("Error loading data:", error);
    alert(
      "Failed to load data. Make sure you are running a local server (python -m http.server) and ran scripts/consolidate_results.py",
    );
  }
}

function updateMetrics(data) {
  const total = data.length;
  const successful = data.filter((r) => r.status === "SUCCESS").length;
  const successRate = total > 0 ? Math.round((successful / total) * 100) : 0;

  // Calculate Real Agentic Avg Duration
  const realRuns = data.filter(
    (r) => r.mode === "REAL" && r.status === "SUCCESS",
  );
  const avgDuration =
    realRuns.length > 0
      ? Math.round(
          realRuns.reduce((acc, r) => acc + r.duration, 0) / realRuns.length,
        )
      : 0;

  document.getElementById("total-runs").textContent = total;
  document.getElementById("success-rate").textContent = `${successRate}%`;
  document.getElementById("avg-latency").textContent = `${avgDuration}s`;
}

function renderCharts(data) {
  const ctxLatency = document.getElementById("latencyChart").getContext("2d");

  // Group by Type (Agentic vs Baseline) and Mode (Real vs Mock)
  const metrics = {
    agentic_real: [],
    baseline_real: [],
    agentic_mock: [],
    baseline_mock: [],
  };

  data.forEach((r) => {
    if (r.status !== "SUCCESS") return;
    const key = `${r.type.toLowerCase()}_${r.mode.toLowerCase()}`;
    if (metrics[key]) metrics[key].push(r.duration);
  });

  const avg = (arr) =>
    arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;

  new Chart(ctxLatency, {
    type: "bar",
    data: {
      labels: [
        "Agentic (Mock)",
        "Baseline (Mock)",
        "Agentic (Real)",
        "Baseline (Real)",
      ],
      datasets: [
        {
          label: "Avg Duration (s)",
          data: [
            avg(metrics.agentic_mock),
            avg(metrics.baseline_mock),
            avg(metrics.agentic_real),
            avg(metrics.baseline_real),
          ],
          backgroundColor: [
            "rgba(54, 162, 235, 0.5)",
            "rgba(255, 99, 132, 0.5)",
            "rgba(54, 162, 235, 1)",
            "rgba(255, 99, 132, 1)",
          ],
          borderColor: [
            "rgba(54, 162, 235, 1)",
            "rgba(255, 99, 132, 1)",
            "rgba(54, 162, 235, 1)",
            "rgba(255, 99, 132, 1)",
          ],
          borderWidth: 1,
        },
      ],
    },
    options: {
      scales: {
        y: { beginAtZero: true },
      },
    },
  });
}

function renderTable(data) {
  const tbody = document.querySelector("#runs-table tbody");
  tbody.innerHTML = "";

  // Sort by timestamp desc
  const sorted = [...data].sort(
    (a, b) => new Date(b.timestamp) - new Date(a.timestamp),
  );
  const recent = sorted.slice(0, 10);

  recent.forEach((run) => {
    const tr = document.createElement("tr");
    const badgeClass =
      run.type === "BASELINE" ? "badge-baseline" : "badge-agentic";
    const statusClass =
      run.status === "SUCCESS" ? "status-success" : "status-failed";

    tr.innerHTML = `
            <td>${run.experiment_id.substring(0, 8)}</td>
            <td><span class="badge ${badgeClass}">${run.type}</span></td>
            <td>${run.learner}</td>
            <td>${run.duration.toFixed(1)}s</td>
            <td class="${statusClass}">${run.status}</td>
            <td>${new Date(run.timestamp).toLocaleTimeString()}</td>
        `;
    tbody.appendChild(tr);
  });
}

// Initial Load
loadData();
