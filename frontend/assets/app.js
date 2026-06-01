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

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('prediction-form');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    clearErrors();
    const values = getFormValues();
    const errors = validateForm(values);
    if (Object.keys(errors).length > 0) {
      displayErrors(errors);
      return;
    }
    setLoading(true);
    // Issue 002 handles the API call
  });
});
