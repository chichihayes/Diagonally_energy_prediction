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
  document.getElementById('result-cost').textContent = `₦${data.estimated_cost_ngn}`;
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

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('prediction-form');
  if (!form) return;

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
    '₦' + prediction.estimated_cost_ngn.toFixed(2);
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

if (document.getElementById('hero-card')) {
  document.addEventListener('DOMContentLoaded', loadDashboard);
}
