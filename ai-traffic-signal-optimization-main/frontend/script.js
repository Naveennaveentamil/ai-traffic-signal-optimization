const API = "";

let chart;
const labels = [];
const predSeries = [];
const vehicleSeries = [];
const MAX_POINTS = 24;

function el(id) {
  return document.getElementById(id);
}

function setLoading(show, message) {
  const overlay = el("loading-overlay");
  const text = el("loading-text");
  if (message) text.textContent = message;
  overlay.classList.toggle("hidden", !show);
  overlay.setAttribute("aria-hidden", show ? "false" : "true");
  document.body.style.overflow = show ? "hidden" : "";
}

function showUploadError(msg) {
  const box = el("upload-error");
  if (!msg) {
    box.classList.add("hidden");
    box.textContent = "";
    return;
  }
  box.textContent = msg;
  box.classList.remove("hidden");
}

function applyDashboardFromProcess(data) {
  if (!data || !data.counts) return;
  const c = data.counts;
  el("metric-total").textContent = c.total_vehicles ?? "—";
  el("metric-density").textContent = data.density ?? "—";
  el("lane-north").textContent = c.north ?? 0;
  el("lane-south").textContent = c.south ?? 0;
  el("lane-east").textContent = c.east ?? 0;
  el("lane-west").textContent = c.west ?? 0;
  if (data.signal_state) {
    const s = data.signal_state;
    el("metric-timer").textContent = s.active_green_duration_sec ?? "—";
    const ns = s.north_south?.is_green;
    if (typeof ns === "boolean") setLights(ns);
    const active = ns ? "North–South" : "East–West";
    el("active-corridor").textContent = `Corridor: ${active}`;
  }
}

function setLights(nsGreen) {
  const ns = el("light-ns").querySelectorAll(".bulb");
  const ew = el("light-ew").querySelectorAll(".bulb");
  ns.forEach((b) => b.classList.remove("on"));
  ew.forEach((b) => b.classList.remove("on"));
  if (nsGreen) {
    ns[2].classList.add("on");
    ew[0].classList.add("on");
  } else {
    ns[0].classList.add("on");
    ew[2].classList.add("on");
  }
}

async function fetchJson(path, options) {
  const res = await fetch(API + path, options);
  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    throw new Error(text || `HTTP ${res.status}`);
  }
  if (!res.ok) throw new Error(data.error || data.message || `HTTP ${res.status}`);
  return data;
}

async function pollSignal() {
  const data = await fetchJson("/api/get_signal");
  const s = data.signal_state;
  const ns = s.north_south.is_green;
  setLights(ns);

  const active = ns ? "North–South" : "East–West";
  el("active-corridor").textContent = `Corridor: ${active}`;
  el("metric-timer").textContent = s.active_green_duration_sec ?? "—";

  el("metric-density").textContent = s.density ?? "—";

  const alert = el("alert-emergency");
  if (data.emergency?.active || data.last_emergency_detected) {
    alert.classList.remove("hidden");
    alert.textContent = data.emergency?.active
      ? "Emergency corridor override active"
      : "Emergency vehicle detected (last run)";
  } else {
    alert.classList.add("hidden");
  }
}

async function pollPredict() {
  const data = await fetchJson("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  el("metric-ml").textContent = data.level;
  el("metric-ml-sub").textContent = `Score ${data.prediction.toFixed(1)} · vehicles used: ${data.vehicle_count_used}`;

  const t = new Date().toLocaleTimeString();
  labels.push(t);
  predSeries.push(data.prediction);
  vehicleSeries.push(data.vehicle_count_used);
  if (labels.length > MAX_POINTS) {
    labels.shift();
    predSeries.shift();
    vehicleSeries.shift();
  }
  chart.data.labels = labels;
  chart.data.datasets[0].data = predSeries;
  chart.data.datasets[1].data = vehicleSeries;
  chart.update("none");
}

function setBusy(busy) {
  el("btn-run-yolo").disabled = busy;
  el("btn-upload-analyze").disabled = busy || !el("input-video").files?.length;
  el("input-video").disabled = busy;
}

async function runVideo() {
  showUploadError("");
  setBusy(true);
  setLoading(true, "Running sample detection…");
  try {
    const data = await fetchJson("/api/process_video", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source: "file",
        path: "../ai/dataset/sample_traffic.mp4",
        max_frames: 30,
      }),
    });
    applyDashboardFromProcess(data);
  } catch (e) {
    console.error(e);
    showUploadError(e.message || "Sample detection failed.");
    el("metric-total").textContent = "—";
  } finally {
    setLoading(false);
    setBusy(false);
  }
}

async function uploadAndAnalyze() {
  const input = el("input-video");
  const file = input.files && input.files[0];
  if (!file) {
    showUploadError("Choose a video file first.");
    return;
  }

  showUploadError("");
  setBusy(true);
  setLoading(true, "Uploading video…");

  const fd = new FormData();
  fd.append("video", file, file.name);
  fd.append("max_frames", "40");

  try {
    setLoading(true, "Running YOLO on your video…");
    const res = await fetch(API + "/api/upload_video", {
      method: "POST",
      body: fd,
    });
    if (res.status === 413) {
      throw new Error(
        "File too large. Use a smaller clip or set MAX_UPLOAD_MB in the server environment."
      );
    }
    const text = await res.text();
    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      throw new Error(text || `Server error (${res.status})`);
    }
    if (!res.ok) {
      throw new Error(data.error || `Upload failed (${res.status})`);
    }
    applyDashboardFromProcess(data);
    showUploadError("");
  } catch (e) {
    console.error(e);
    const msg =
      e.message && e.message.includes("413")
        ? "File too large. Reduce size or raise MAX_UPLOAD_MB on the server."
        : e.message || "Upload failed.";
    showUploadError(msg);
  } finally {
    setLoading(false);
    setBusy(false);
  }
}

function onVideoSelected() {
  const input = el("input-video");
  const file = input.files && input.files[0];
  el("btn-upload-analyze").disabled = !file;
  el("upload-filename").textContent = file ? file.name : "No file selected";
  showUploadError("");
}

async function toggleEmergency() {
  const on = el("emergency-toggle").checked;
  await fetchJson("/api/emergency", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ active: on, corridor: "north_south" }),
  });
}

function initChart() {
  const ctx = el("chart-traffic").getContext("2d");
  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "ML congestion",
          data: [],
          borderColor: "#3d8bfd",
          tension: 0.25,
          yAxisID: "y",
        },
        {
          label: "Vehicle count (last)",
          data: [],
          borderColor: "#22c55e",
          tension: 0.25,
          yAxisID: "y1",
        },
      ],
    },
    options: {
      responsive: true,
      interaction: { mode: "index", intersect: false },
      scales: {
        y: {
          type: "linear",
          position: "left",
          min: 0,
          max: 100,
          grid: { color: "rgba(148,163,184,0.15)" },
          ticks: { color: "#94a3b8" },
        },
        y1: {
          type: "linear",
          position: "right",
          min: 0,
          grid: { drawOnChartArea: false },
          ticks: { color: "#94a3b8" },
        },
        x: {
          ticks: { maxRotation: 0, color: "#94a3b8" },
          grid: { color: "rgba(148,163,184,0.1)" },
        },
      },
      plugins: {
        legend: { labels: { color: "#cbd5e1" } },
      },
    },
  });
}

async function boot() {
  initChart();
  el("btn-run-yolo").addEventListener("click", runVideo);
  el("btn-upload-analyze").addEventListener("click", uploadAndAnalyze);
  el("input-video").addEventListener("change", onVideoSelected);
  el("emergency-toggle").addEventListener("change", toggleEmergency);

  await runVideo().catch(() => {});
  setInterval(() => {
    pollSignal().catch(console.error);
    pollPredict().catch(console.error);
  }, 2000);
  pollSignal().catch(console.error);
  pollPredict().catch(console.error);
}

document.addEventListener("DOMContentLoaded", boot);
