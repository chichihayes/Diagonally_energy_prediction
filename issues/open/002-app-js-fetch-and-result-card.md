---
epic: E1-instant-appliance-prediction
feature: F2
issue: 002
slug: app-js-fetch-and-result-card
---

# 002 — Implement app.js fetch call and result card

## Goal

After a homeowner submits a valid form, simple.html POSTs to the API and renders
the predicted Wh, kWh, estimated cost in NGN, and the five weather factors the
model used — or shows a clear inline error message if the API returns a non-200
status.

## User Story

As a homeowner, I want to see my predicted energy usage and estimated cost
immediately after I submit, and I want to know which weather readings were used,
so I understand what drove the prediction.

## Reference Docs

- `docs/api-contracts.md` — POST /api/v1/predict/simple request and response shapes
- `docs/architecture.md` — frontend file layout

## Acceptance Criteria

- [ ] On valid form submit, `fetch('POST /api/v1/predict/simple', { lights, T1, location })` is called
- [ ] On 200 response: result card renders with `predicted_wh`, `predicted_kwh`, `estimated_cost_ngn`
- [ ] Weather factors grid shows all five values: `T_out`, `RH_out`, `Windspeed`, `Visibility`, `Tdewpoint`
- [ ] `predicted_wh` is the hero value — displayed largest
- [ ] On non-200 response: inline error message shows HTTP status and reason text
- [ ] Spinner clears and button re-enables after success or error
- [ ] Result card is hidden until a successful response is received

## Files to Modify

- `frontend/assets/app.js` — add `submitPrediction()`, `renderResult()`, `renderError()`
- `frontend/simple.html` — add result card HTML (hidden by default), wire up error container

## Out of Scope

- Saving predictions to Supabase (that happens server-side)
- Prediction history display (F3)
- Smart Home or forecast forms

## Implementation Plan

### Step 1 — Write `submitPrediction(payload)` function

**Test:** Mock `fetch` to return `{ ok: true, json: async () => mockResponse }`.
Call `submitPrediction({ lights: 100, T1: 22, location: 'Lagos' })`.
Assert `fetch` was called with `method: 'POST'`, `Content-Type: application/json`,
and body `JSON.stringify({ lights: 100, T1: 22, location: 'Lagos' })`.

**File:** `frontend/assets/app.js`

```js
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
```

### Step 2 — Write `renderResult(data)` function

**Test:** Call `renderResult` with the exact mock API response below.
Assert each DOM element contains the expected text.

Mock response:
```json
{
  "predicted_wh": 60.5,
  "predicted_kwh": 0.0605,
  "estimated_cost_ngn": 5.18,
  "weather_factors": {
    "T_out": 28.4,
    "RH_out": 82.0,
    "Windspeed": 3.1,
    "Visibility": 10.0,
    "Tdewpoint": 25.1
  }
}
```

| DOM selector | Expected inner text |
|---|---|
| `#result-wh` | `"60.5 Wh"` |
| `#result-kwh` | `"0.0605 kWh"` |
| `#result-cost` | `"₦5.18"` |
| `#result-t-out` | `"28.4 °C"` |
| `#result-rh-out` | `"82.0 %"` |
| `#result-windspeed` | `"3.1 m/s"` |
| `#result-visibility` | `"10.0 km"` |
| `#result-tdewpoint` | `"25.1 °C"` |
| `#result-card` | visible (no `hidden` class) |

**File:** `frontend/assets/app.js`

```js
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
```

### Step 3 — Write `renderError(message)` function

**Test:** Call `renderError('500 — Internal Server Error')`.
Assert `#error-message` inner text equals `'500 — Internal Server Error'`
and `#error-container` does not have class `hidden`.

**File:** `frontend/assets/app.js`

```js
function renderError(message) {
  document.getElementById('error-message').textContent = message;
  document.getElementById('error-container').classList.remove('hidden');
}
```

### Step 4 — Wire everything into the form submit handler (from Issue 001)

**Test (manual):** With the API running locally, submit `lights=100, T1=22, city=Lagos`.
Confirm spinner appears, result card renders with all 8 values, spinner clears.

**File:** `frontend/assets/app.js`

```js
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  clearErrors();
  const errors = validateForm(getFormValues());
  if (Object.keys(errors).length > 0) { displayErrors(errors); return; }
  setLoading(true);
  try {
    const data = await submitPrediction(getFormValues());
    renderResult(data);
  } catch (err) {
    renderError(err.message);
  } finally {
    setLoading(false);
  }
});
```

### Step 5 — Add result card and error container HTML to simple.html

**Test (manual):** Inspect DOM before submit — `#result-card` has class `hidden`.
After successful submit — `hidden` is removed. Hero value `#result-wh` uses
larger font (e.g. `text-4xl`). Weather grid shows all five values in a 2-column
or 3-column grid.

**File:** `frontend/simple.html`

```html
<!-- Result card — hidden until API responds -->
<div id="result-card" class="hidden mt-6 p-6 bg-white rounded-2xl shadow">
  <p class="text-4xl font-bold" id="result-wh"></p>
  <p id="result-kwh"></p>
  <p id="result-cost"></p>
  <div class="grid grid-cols-2 gap-2 mt-4">
    <span>Outside temp:</span><span id="result-t-out"></span>
    <span>Humidity:</span><span id="result-rh-out"></span>
    <span>Wind speed:</span><span id="result-windspeed"></span>
    <span>Visibility:</span><span id="result-visibility"></span>
    <span>Dew point:</span><span id="result-tdewpoint"></span>
  </div>
</div>

<!-- Error container — hidden until API error -->
<div id="error-container" class="hidden mt-4 p-4 bg-red-50 text-red-700 rounded-lg">
  <p id="error-message"></p>
</div>
```

## Git

- **Branch:** `feat/002-app-js-fetch-result-card`
- **Commit format:** `feat(frontend): add fetch call and result card to simple.html`
- **PR title:** `feat: app.js fetch + result card for simple prediction (#002)`
