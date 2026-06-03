function validateForm({ lights, t1, city }) {
  const errors = {};
  if (lights === '' || lights === null || lights === undefined) {
    errors.lights = 'Lights is required';
  } else if (Number(lights) < 0) {
    errors.lights = 'Lights must be 0 or greater';
  }
  if (t1 === '' || t1 === null || t1 === undefined) {
    errors.t1 = 'T1 is required';
  } else if (Number(t1) < -20 || Number(t1) > 60) {
    errors.t1 = 'Temperature must be between −20 and 60 °C';
  }
  if (!city || city.trim() === '') {
    errors.city = 'City is required';
  }
  return errors;
}

function getFormValues() {
  return {
    lights: document.getElementById('lights').value,
    t1: document.getElementById('t1').value,
    city: document.getElementById('city').value,
  };
}

function clearErrors() {
  ['lights', 't1', 'city'].forEach((field) => {
    const el = document.getElementById(`${field}-error`);
    if (el) {
      el.textContent = '';
      el.hidden = true;
    }
    const input = document.getElementById(field);
    if (input) input.classList.remove('border-red-500');
  });
}

function displayErrors(errors) {
  Object.entries(errors).forEach(([field, message]) => {
    const el = document.getElementById(`${field}-error`);
    if (el) {
      el.textContent = message;
      el.hidden = false;
    }
    const input = document.getElementById(field);
    if (input) input.classList.add('border-red-500');
  });
}

function setLoading(on) {
  const btn = document.getElementById('submit-btn');
  btn.disabled = on;
  btn.innerHTML = on
    ? '<svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg>Loading…'
    : 'Get Prediction';
}

async function submitPrediction(payload) {
  const res = await fetch('/api/v1/predict/simple', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} — ${text}`);
  }
  return res.json();
}

function renderResult(data) {
  document.getElementById('result-wh').textContent = `${data.predicted_wh} Wh`;
  document.getElementById('result-kwh').textContent = `${data.predicted_kwh} kWh`;
  document.getElementById('result-cost').textContent = `£${data.estimated_cost_gbp}`;
  const wf = data.weather_factors;
  document.getElementById('result-t-out').textContent = `${wf.T_out} °C`;
  document.getElementById('result-rh-out').textContent = `${wf.RH_out} %`;
  document.getElementById('result-windspeed').textContent = `${wf.Windspeed} m/s`;
  document.getElementById('result-visibility').textContent = `${wf.Visibility} km`;
  document.getElementById('result-tdewpoint').textContent = `${wf.Tdewpoint} °C`;
  document.getElementById('result-card').classList.remove('hidden');
}

function renderError(message) {
  document.getElementById('error-message').textContent = message;
  document.getElementById('error-container').classList.remove('hidden');
}

async function loadHistory() {
  const tbody = document.getElementById('history-body');
  if (!tbody) return;
  const res = await fetch('/api/v1/predictions?tier=simple&limit=10');
  const rows = await res.json();

  if (!rows.length) {
    tbody.innerHTML = `
      <tr id="history-empty">
        <td colspan="4" class="px-4 py-6 text-center text-gray-400">No predictions yet</td>
      </tr>`;
    return;
  }

  tbody.innerHTML = rows.map(row => {
    const time = new Date(row.created_at).toLocaleString('en-GB', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
    return `<tr class="border-t border-gray-100 hover:bg-gray-50">
      <td class="px-4 py-3 whitespace-nowrap">${time}</td>
      <td class="px-4 py-3">${row.predicted_wh.toFixed(1)}</td>
      <td class="px-4 py-3">${row.predicted_kwh.toFixed(4)}</td>
      <td class="px-4 py-3">£${row.estimated_cost_gbp.toFixed(2)}</td>
    </tr>`;
  }).join('');
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('prediction-form');
  if (!form) return;

  loadHistory();

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearErrors();
    document.getElementById('error-container').classList.add('hidden');
    document.getElementById('result-card').classList.add('hidden');
    const values = getFormValues();
    const errors = validateForm(values);
    if (Object.keys(errors).length > 0) {
      displayErrors(errors);
      return;
    }
    setLoading(true);
    try {
      const data = await submitPrediction({
        lights: Number(values.lights),
        T1: Number(values.t1),
        location: values.city,
      });
      renderResult(data);
      await loadHistory();
    } catch (err) {
      renderError(err.message);
    } finally {
      setLoading(false);
    }
  });
});

// ── Dashboard (dashboard.html) ────────────────────────────────────────────────

async function fetchLatestPrediction() {
  const resp = await fetch('/api/v1/predictions?tier=full&limit=1');
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  const data = await resp.json();
  if (data.length === 0) throw new Error('empty');
  return data[0];
}

function populateHeroCard(prediction) {
  document.getElementById('predicted-wh').textContent = prediction.predicted_wh;
  document.getElementById('predicted-kwh').textContent = prediction.predicted_kwh;
  document.getElementById('estimated-cost').textContent =
    '£' + prediction.estimated_cost_gbp.toFixed(2);
  document.getElementById('last-updated').textContent =
    new Date(prediction.created_at).toLocaleString();
}

function populateSensorGrid(features) {
  for (let i = 1; i <= 9; i++) {
    const tile = document.querySelector(`[data-room="${i}"]`);
    if (!tile) continue;
    tile.querySelector('.room-temp').textContent = features[`T${i}`];
    tile.querySelector('.room-humidity').textContent = features[`RH_${i}`];
  }
}

function populateWeatherStrip(f) {
  document.getElementById('w-t-out').textContent = f.T_out;
  document.getElementById('w-rh-out').textContent = f.RH_out;
  document.getElementById('w-windspeed').textContent = f.Windspeed;
  document.getElementById('w-visibility').textContent = f.Visibility;
  document.getElementById('w-tdewpoint').textContent = f.Tdewpoint;
}

function showSkeleton() {
  document.getElementById('hero-card').classList.add('animate-pulse');
}

function hideSkeleton() {
  document.getElementById('hero-card').classList.remove('animate-pulse');
}

function showError(message) {
  const banner = document.getElementById('error-banner');
  banner.textContent = message;
  banner.hidden = false;
}

async function loadDashboard() {
  showSkeleton();
  try {
    const prediction = await fetchLatestPrediction();
    populateHeroCard(prediction);
    populateSensorGrid(prediction.input_features);
    populateWeatherStrip(prediction.input_features);
  } catch (err) {
    const msg = err.message === 'empty'
      ? 'No predictions found. Wait for the next scheduled reading.'
      : 'Failed to load dashboard data. Please try again.';
    showError(msg);
  } finally {
    hideSkeleton();
  }
}

async function refreshDashboard() {
  const banner = document.getElementById('error-banner');
  try {
    const prediction = await fetchLatestPrediction();
    banner.hidden = true;
    populateHeroCard(prediction);
    populateSensorGrid(prediction.input_features);
    populateWeatherStrip(prediction.input_features);
  } catch {
    banner.textContent = 'Auto-refresh failed. Showing last known data.';
    banner.hidden = false;
  }
}

function startAutoRefresh(intervalMs) {
  return setInterval(refreshDashboard, intervalMs);
}

const REFRESH_INTERVAL_MS = 15 * 60 * 1000;

function buildSinceParam() {
  return new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
}

function renderHistoryChart(predictions) {
  const canvas = document.getElementById('history-chart');
  const empty  = document.getElementById('chart-empty');

  if (!predictions.length) {
    canvas.hidden = true;
    empty.hidden  = false;
    return;
  }

  const labels      = predictions.map(p =>
    new Date(p.created_at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
  );
  const values      = predictions.map(p => p.predicted_wh);
  const maxVal      = Math.max(...values);
  const pointColors = values.map(v => v === maxVal ? '#ef4444' : '#3b82f6');

  canvas.hidden = false;
  empty.hidden  = true;

  new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Predicted Wh',
        data: values,
        borderColor: '#3b82f6',
        pointBackgroundColor: pointColors,
        tension: 0.3,
        fill: false,
      }]
    },
    options: {
      animation: false,
      scales: {
        y: { title: { display: true, text: 'Wh' } }
      }
    }
  });
}

async function fetchHistoryChart() {
  const since = buildSinceParam();
  const res = await fetch(
    `/api/v1/predictions?tier=full&since=${encodeURIComponent(since)}&limit=96`
  );
  const data = await res.json();
  renderHistoryChart(data);
}

function formatDate(isoString) {
  const d    = new Date(isoString);
  const dd   = String(d.getDate()).padStart(2, '0');
  const mm   = String(d.getMonth() + 1).padStart(2, '0');
  const yyyy = d.getFullYear();
  const hh   = String(d.getHours()).padStart(2, '0');
  const min  = String(d.getMinutes()).padStart(2, '0');
  return `${dd}/${mm}/${yyyy} ${hh}:${min}`;
}

function renderHistoryTable(predictions) {
  const tbody = document.getElementById('history-table-body');
  if (!predictions.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="py-2 text-gray-500">No data yet</td></tr>';
    return;
  }
  tbody.innerHTML = predictions.map(p => `
    <tr class="border-b last:border-0">
      <td class="py-1 pr-4">${formatDate(p.created_at)}</td>
      <td class="py-1 pr-4">${Math.round(p.predicted_wh)}</td>
      <td class="py-1 pr-4">${p.predicted_kwh.toFixed(4)}</td>
      <td class="py-1">£${p.estimated_cost_gbp.toFixed(2)}</td>
    </tr>
  `).join('');
}

async function fetchHistoryTable() {
  const res  = await fetch('/api/v1/predictions?tier=full&limit=10');
  const data = await res.json();
  renderHistoryTable(data);
}

// ── Forecast (forecast.html) ──────────────────────────────────────────────────

function setForecastLoading(on) {
  const btn = document.getElementById('forecast-btn');
  const spinner = document.getElementById('forecast-spinner');
  btn.disabled = on;
  spinner.classList.toggle('hidden', !on);
}

async function fetchForecast24h() {
  const res = await fetch('/api/v1/forecast/24h');
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Server error ${res.status}`);
  }
  return res.json();
}

let chart24h = null;

function render24hChart(data, canvasId) {
  const labels = data.forecast.map(p => {
    const d = new Date(p.hour);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
  });

  const peakIso = data.peak_hour;
  const pointColors = data.forecast.map(p =>
    p.hour === peakIso ? '#f59e0b' : '#6366f1'
  );
  const pointRadii = data.forecast.map(p =>
    p.hour === peakIso ? 6 : 3
  );

  const mainDataset = {
    label: 'Predicted Wh',
    data: data.forecast.map(p => p.predicted_wh),
    borderColor: '#6366f1',
    pointBackgroundColor: pointColors,
    pointRadius: pointRadii,
    tension: 0.3,
    fill: false,
  };

  const upperDataset = {
    label: 'Upper bound',
    data: data.forecast.map(p => p.upper_wh),
    borderColor: 'transparent',
    pointRadius: 0,
    fill: '+1',
    backgroundColor: 'rgba(99,102,241,0.12)',
  };

  const lowerDataset = {
    label: 'Lower bound',
    data: data.forecast.map(p => p.lower_wh),
    borderColor: 'transparent',
    pointRadius: 0,
    fill: false,
  };

  const costs = data.forecast.map(p => p.estimated_cost_gbp);

  if (chart24h) chart24h.destroy();
  const ctx = document.getElementById(canvasId).getContext('2d');
  chart24h = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets: [upperDataset, lowerDataset, mainDataset] },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            afterLabel: (item) => {
              if (item.datasetIndex === 2) {
                return `Cost: £${costs[item.dataIndex].toFixed(2)}`;
              }
              return null;
            },
          },
        },
      },
      scales: {
        x: { title: { display: true, text: 'Hour' } },
        y: { title: { display: true, text: 'Wh' } },
      },
    },
  });
}

async function fetchForecast7d() {
  const res = await fetch('/api/v1/forecast/7d');
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Server error ${res.status}`);
  }
  return res.json();
}

let chart7d = null;

function render7dChart(data, canvasId) {
  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const labels = data.forecast.map(p => {
    const d = new Date(p.date);
    return dayNames[d.getUTCDay()];
  });

  const barColors = labels.map(day =>
    day === data.peak_day ? '#f59e0b' : '#6366f1'
  );

  if (chart7d) chart7d.destroy();
  const ctx = document.getElementById(canvasId).getContext('2d');
  chart7d = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Daily Wh',
        data: data.forecast.map(p => p.predicted_wh),
        backgroundColor: barColors,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { title: { display: true, text: 'Day' } },
        y: { title: { display: true, text: 'Wh' } },
      },
    },
  });
}

function formatGBP(amount) {
  return '£' + amount.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function renderBillCard(bill) {
  const card = document.getElementById('bill-card');
  card.innerHTML = `
    <div class="grid grid-cols-3 gap-4 text-center">
      <div class="bg-green-50 rounded-xl p-4">
        <p class="text-xs text-green-600 font-medium uppercase tracking-wide mb-1">Optimistic</p>
        <p data-bill="optimistic" class="text-xl font-bold text-green-700">${formatGBP(bill.optimistic_gbp)}</p>
      </div>
      <div class="bg-indigo-50 rounded-xl p-5 ring-2 ring-indigo-400">
        <p class="text-xs text-indigo-600 font-medium uppercase tracking-wide mb-1">Most Likely</p>
        <p data-bill="most-likely" class="text-2xl font-extrabold text-indigo-700">${formatGBP(bill.most_likely_gbp)}</p>
      </div>
      <div class="bg-red-50 rounded-xl p-4">
        <p class="text-xs text-red-600 font-medium uppercase tracking-wide mb-1">Pessimistic</p>
        <p data-bill="pessimistic" class="text-xl font-bold text-red-700">${formatGBP(bill.pessimistic_gbp)}</p>
      </div>
    </div>
  `;
}

if (document.getElementById('forecast-form')) {
  document.getElementById('forecast-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const errorEl = document.getElementById('forecast-error');
    errorEl.classList.add('hidden');
    errorEl.textContent = '';
    ['section-24h', 'section-7d', 'section-bill'].forEach(id =>
      document.getElementById(id).classList.add('hidden')
    );

    setForecastLoading(true);
    try {
      const [data24h, data7d] = await Promise.all([
        fetchForecast24h(),
        fetchForecast7d(),
      ]);

      render24hChart(data24h, 'chart-24h');
      document.getElementById('section-24h').classList.remove('hidden');

      render7dChart(data7d, 'chart-7d');
      document.getElementById('section-7d').classList.remove('hidden');

      renderBillCard(data7d.projected_week_bill);
      document.getElementById('section-bill').classList.remove('hidden');
    } catch (err) {
      errorEl.textContent = err.message;
      errorEl.classList.remove('hidden');
    } finally {
      setForecastLoading(false);
    }
  });
}

if (document.getElementById('hero-card')) {
  document.addEventListener('DOMContentLoaded', async () => {
    await loadDashboard();
    fetchHistoryChart();
    fetchHistoryTable();
    setInterval(() => {
      refreshDashboard();
      fetchHistoryChart();
      fetchHistoryTable();
    }, REFRESH_INTERVAL_MS);
  });
}
