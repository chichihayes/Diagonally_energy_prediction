---
epic: E1-instant-appliance-prediction
feature: F2
issue: 001
slug: simple-html-form
---

# 001 — Build simple.html form

## Goal

A homeowner opens simple.html and sees a validated three-field form that prevents
submission of bad input before any API call is made.

## User Story

As a homeowner with no sensors, I want inline feedback when I enter an invalid
lights value, temperature, or leave the city blank, so I never waste a round-trip
on bad data.

## Reference Docs

- `docs/api-contracts.md` — POST /api/v1/predict/simple request shape (lights, T1, location)
- `docs/architecture.md` — frontend file layout (frontend/simple.html, frontend/assets/app.js)

## Acceptance Criteria

- [ ] simple.html renders three labelled inputs: Lights (Wh, number), T1 (°C, number), City (text)
- [ ] Submitting with any empty field shows an inline error beneath that field without a page reload
- [ ] Lights value < 0 shows inline error "Lights must be 0 or greater"
- [ ] T1 outside −20 to 60 shows inline error "Temperature must be between −20 and 60 °C"
- [ ] All inputs valid → "Get Prediction" button disables and spinner appears
- [ ] Page is responsive: single-column on mobile (< 640 px), centred card on desktop

## Files to Modify

- `frontend/simple.html` — create (does not exist yet)
- `frontend/assets/style.css` — add any custom styles not covered by Tailwind

## Out of Scope

- Fetching data or calling the API (Issue 002)
- Displaying the result card (Issue 002)
- Prediction history table (F3)
- Smart Home tier form

## Implementation Plan

### Step 1 — Scaffold simple.html with Tailwind via CDN

**Test (manual):** Open simple.html in a browser. Confirm three labelled inputs and
a "Get Prediction" button render without console errors.

**File:** `frontend/simple.html`

```html
<!-- minimum structure -->
<input id="lights" type="number" min="0" placeholder="e.g. 100" required />
<input id="t1" type="number" min="-20" max="60" placeholder="e.g. 22" required />
<input id="city" type="text" placeholder="e.g. Lagos" required />
<button id="submit-btn" type="submit">Get Prediction</button>
```

### Step 2 — Add inline validation function

**Test (automated, `tests/test_form_validation.js` or manual console check):**

| Call | Expected |
|---|---|
| `validateForm({ lights: -1, t1: 22, city: 'Lagos' })` | `{ lights: 'Lights must be 0 or greater' }` |
| `validateForm({ lights: 100, t1: 99, city: 'Lagos' })` | `{ t1: 'Temperature must be between −20 and 60 °C' }` |
| `validateForm({ lights: 100, t1: 22, city: '' })` | `{ city: 'City is required' }` |
| `validateForm({ lights: 100, t1: 22, city: 'Lagos' })` | `{}` (no errors) |

**File:** `frontend/assets/app.js`

```js
function validateForm({ lights, t1, city }) {
  const errors = {};
  if (lights === '' || lights === null) errors.lights = 'Lights is required';
  else if (Number(lights) < 0) errors.lights = 'Lights must be 0 or greater';
  if (t1 === '' || t1 === null) errors.t1 = 'T1 is required';
  else if (Number(t1) < -20 || Number(t1) > 60) errors.t1 = 'Temperature must be between −20 and 60 °C';
  if (!city || city.trim() === '') errors.city = 'City is required';
  return errors;
}
```

### Step 3 — Wire validation to form submit, show errors inline

**Test (manual):** Click submit with lights = −5. Confirm error text appears
beneath the lights input. Confirm button is NOT disabled (no spinner) because
submission was blocked.

**File:** `frontend/simple.html` (event listener in `<script>` tag or app.js)

```js
form.addEventListener('submit', (e) => {
  e.preventDefault();
  clearErrors();
  const errors = validateForm(getFormValues());
  if (Object.keys(errors).length > 0) {
    displayErrors(errors);
    return;
  }
  setLoading(true);
  // Issue 002 handles the API call
});
```

### Step 4 — Spinner and disabled state

**Test (manual):** Submit a valid form. Confirm the button text changes to a
spinner icon and `disabled` attribute is set. (API call will fail at this stage
since Issue 002 is not implemented — that is expected.)

**File:** `frontend/simple.html` or `frontend/assets/app.js`

```js
function setLoading(on) {
  const btn = document.getElementById('submit-btn');
  btn.disabled = on;
  btn.textContent = on ? 'Loading…' : 'Get Prediction';
}
```

### Step 5 — Responsive layout

**Test (manual):** Resize browser window to 375 px wide. Confirm inputs stack
vertically and are full-width. At 1024 px wide, confirm the card is centred with
`max-w-lg` or equivalent.

**File:** `frontend/simple.html` (Tailwind classes: `max-w-lg mx-auto`, `w-full`)

## Git

- **Branch:** `feat/001-simple-html-form`
- **Commit format:** `feat(frontend): build simple.html three-field form with inline validation`
- **PR title:** `feat: simple.html prediction form with inline validation (#001)`
