# docs/decisions.md — Diagonally Energy Prediction

## ADR-001: Train both Random Forest and XGBoost; save the best

Train both models on the same dataset and evaluate R² on a held-out 20% test split. Save the one with the higher R² as the production model. Both are saved as separate `.joblib` files so the losing model can be inspected.

**Why:** RF is robust to multicollinearity across 28 correlated T/RH features and requires no feature scaling. XGBoost typically outperforms on tabular regression. Training both and picking the winner is low-cost and eliminates the need to guess upfront.

---

## ADR-002: Two separate model files (model_full, model_simple)

`model_full.joblib` is trained on all 25 features. `model_simple.joblib` is trained separately on 7 features (lights, T1, T_out, RH_out, Windspeed, Visibility, Tdewpoint).

**Why:** Basic tier users have no room sensors. A model trained on 25 features cannot run on 7 inputs. Training a dedicated 7-feature model on the same dataset lets Basic tier users get meaningful predictions without imputing the missing 18 sensor values.

---

## ADR-003: rv1 and rv2 dropped at preprocessing

These two columns are dropped in `data_loader.py` before any feature matrix is built.

**Why:** Random noise variables added by the UCI dataset authors to test model robustness. No predictive value. Keeping them would add noise and inflate feature count.

---

## ADR-004: lights kept as input feature, not folded into target

`lights` is a separate sensor reading from the `Appliances` target. It is treated as an input feature for both tiers.

**Why:** The dataset authors measured lights and appliances with separate sensors. lights energy is not included in the Appliances total — it is an independent reading that correlates with overall home activity.

---

## ADR-005: OpenWeatherMap free tier, cached 10 minutes in memory

A single `weather.py` module wraps the OWM Current Weather API. Responses are stored in a module-level dict keyed by city name, with a timestamp. Any call within 10 minutes of the last fetch returns the cached value.

**Why:** Free tier rate limits make per-request calls risky at scale. 10-minute caching aligns with the dataset's own 10-minute measurement interval and keeps predictions well under the 2-second target.

---

## ADR-006: Supabase (Postgres) for prediction storage

Every successful prediction is inserted into a `predictions` table in Supabase via the Supabase Python client.

**Why:** Managed Postgres with a simple REST/Python SDK — no infrastructure to run. Enables the Basic tier history view and Smart Home dashboard with no extra backend work.

---

## ADR-007: APScheduler runs inside the FastAPI process

APScheduler is started in the FastAPI lifespan event (`main.py`) and fires every 15 minutes to submit Smart Home sensor readings to `/api/v1/predict/full`.

**Why:** No separate worker process or queue needed for a demo. APScheduler integrates directly with FastAPI's async lifecycle. If a separate worker is needed later, the scheduler can be extracted without changing `routes.py`.

---

## ADR-008: NERC tariff rate stored in environment variable

The cost calculation is `predicted_kwh × NERC_TARIFF_NGN_PER_KWH`. The rate is read from the environment at startup — never hardcoded.

**Why:** Electricity tariffs change. An env var allows the rate to be updated without a code change or redeploy.

---

## ADR-009: joblib for model persistence

Both models are saved and loaded with `joblib.dump` / `joblib.load`.

**Why:** Standard for scikit-learn. Faster load than pickle for numpy arrays. Models are loaded once at startup as module-level singletons — never reloaded per request.

---

## ADR-010: No user authentication for the demo

There is no login, session, or token system.

**Why:** Out of scope per PRD. Adding auth at demo stage would double implementation time with no user-facing value. Can be added as a separate feature if the system moves to production.

---

## ADR-011: Pure HTML + JS + Tailwind CDN for frontend

No JavaScript framework, no build step, no bundler. Tailwind is loaded from CDN.

**Why:** Fastest path to a responsive demo frontend. A framework would require a build pipeline, node_modules, and deployment complexity that adds no value for a single-page prediction form and dashboard.
