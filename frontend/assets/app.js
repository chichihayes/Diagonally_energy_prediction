// ── Forecast form (forecast.html) ────────────────────────────────────────────

function _updateDerivedDateFields() {
  const val = document.getElementById('input-date').value;
  if (!val) return;
  const d = new Date(val + 'T00:00:00');
  const dow = (d.getDay() + 6) % 7; // JS Sunday=0 → Monday=0
  document.getElementById('input-dow').value     = dow;
  document.getElementById('input-month').value   = d.getMonth() + 1;
  document.getElementById('input-weekend').value = dow >= 5 ? 1 : 0;
}

function _getFormValues() {
  return {
    date:                  document.getElementById('input-date').value,
    lag_1:                 parseFloat(document.getElementById('input-lag1').value),
    lag_7:                 parseFloat(document.getElementById('input-lag7').value),
    rolling_mean_7:        parseFloat(document.getElementById('input-roll7').value),
    heater_lag_1:          parseFloat(document.getElementById('input-heater-lag1').value),
    heater_lag_7:          parseFloat(document.getElementById('input-heater-lag7').value),
    heater_rolling_mean_7: parseFloat(document.getElementById('input-heater-roll7').value),
    temp_mean_c:           parseFloat(document.getElementById('input-temp-mean').value),
    temp_min_c:            parseFloat(document.getElementById('input-temp-min').value),
  };
}

const _dateInput = document.getElementById('input-date');
if (_dateInput) {
  _dateInput.addEventListener('change', _updateDerivedDateFields);
  _updateDerivedDateFields();
}

function _showResultCard(result) {
  const card = document.getElementById('result-card');
  if (!card) return;

  document.getElementById('result-date').textContent = result.date;
  document.getElementById('result-cost').textContent = '£' + result.estimated_cost_gbp.toFixed(2);
  document.getElementById('result-wh').textContent   = Math.round(result.predicted_wh).toLocaleString() + ' Wh';
  document.getElementById('result-kwh').textContent  = result.predicted_kwh.toFixed(3) + ' kWh';
  document.getElementById('result-temp').textContent =
    (result.temp_mean_c != null ? result.temp_mean_c.toFixed(1) : '—') + '°C mean / ' +
    (result.temp_min_c  != null ? result.temp_min_c.toFixed(1)  : '—') + '°C min';

  card.classList.remove('hidden');
  card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function _submitPrediction(params) {
  const btn     = document.getElementById('predict-btn');
  const errorEl = document.getElementById('predict-error');
  const card    = document.getElementById('result-card');

  if (btn)     btn.disabled = true;
  if (errorEl) { errorEl.classList.add('hidden'); errorEl.textContent = ''; }
  if (card)    card.classList.add('hidden');

  try {
    const res = await fetch('/api/v1/forecast/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Server error ${res.status}`);
    }
    _showResultCard(await res.json());
  } catch (err) {
    if (errorEl) { errorEl.textContent = err.message; errorEl.classList.remove('hidden'); }
  } finally {
    if (btn) btn.disabled = false;
  }
}

if (document.getElementById('predict-form')) {
  document.getElementById('predict-form').addEventListener('submit', e => {
    e.preventDefault();
    _submitPrediction(_getFormValues());
  });
}

