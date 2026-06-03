# UI/UX Design Specification — Diagonally Energy Prediction

**Version:** 2.0
**Date:** 2026-06-03
**Status:** Current
**Source:** REFIT Smart Home Dataset (House 1), UK household

## Change Log

| Version | Date | Author | Changes |
|---|---|---|---|
| 2.0 | 2026-06-03 | — | Rewrite — removed Basic tier, weather, NGN; 2-page app, GBP |
| 1.0 | 2026-06-01 | — | Initial spec (deprecated) |

---

## 1. Product Context

Diagonally Energy Prediction is a read-only web dashboard showing real household appliance energy data from the REFIT Smart Home Dataset (House 1, UK). A background scheduler replays the test split (Dec 16 – Jan 2 2014) every 15 minutes, storing per-appliance Wh readings and estimated GBP cost in Supabase. The UI has no forms and requires no user input — it is a live data display. Currency is GBP (£). There is no authentication.

---

## 2. Design Principles

1. **Numbers first.** The predicted Wh, kWh, and GBP cost are the product. Every element exists to surface those numbers or navigate between views of them.
2. **One screen, one job.** `dashboard.html` shows what is happening now. `forecast.html` shows what will happen next. No page does both jobs.
3. **Instant or explained.** If a number is available, show it. If loading, show a skeleton. If failed, show an inline error with a retry. Never show a blank space.
4. **Mobile first.** Design for 375px first; scale up gracefully.
5. **GBP.** All cost values use `£` prefix, 2 decimal places. Never use NGN or any other currency.

---

## 3. User Archetype & Primary Flows

**Smart Home viewer:** Wants to glance at current household energy consumption and project next week's electricity bill without entering anything.

**Primary flows:**
1. **Dashboard check:** Open `dashboard.html` → see current aggregate Wh, per-appliance breakdown, and cost → read history chart.
2. **Forecast check:** Open `forecast.html` → click "Get Forecast" → see 24h area chart, 7-day bar chart, weekly bill range in GBP → optionally expand model leaderboard.

---

## 4. Information Architecture

```
Root
├── dashboard.html   — live per-appliance readings + 24h history chart
└── forecast.html    — 24h/7d forecast charts + weekly bill + model leaderboard
```

Both pages are Level 1 peers. Navigation is lateral only — no parent/child hierarchy. No page requires prior navigation through another page.

---

## 5. Navigation System

### 5.1 Primary navigation paradigm

Two-link top nav bar, sticky, on both pages.

- **Desktop (≥768px):** Horizontal nav bar. Logo left. "Dashboard" and "Forecast" links right. Active page: teal text + 2px teal underline.
- **Mobile (<768px):** Logo left, hamburger right. Tapping opens full-width dropdown with both links stacked.

### 5.2 Deep link map

| URL | Screen | Behavior |
|---|---|---|
| `dashboard.html` | Live Dashboard | Shows skeleton → loads latest prediction immediately |
| `forecast.html` | Forecast | Shows empty state → user clicks "Get Forecast" |

### 5.3 Back behavior

No in-app back buttons. Navigation is via the persistent top nav or browser controls only.

---

## 6. Screen Inventory

| # | Screen | File | Primary action | Entry points |
|---|---|---|---|---|
| 1 | Live Dashboard | `dashboard.html` | Read current consumption | Direct URL, nav bar |
| 2 | Forecast | `forecast.html` | Click "Get Forecast" | Nav bar, direct URL |

---

## 7. Screen Specifications

### 7.1 Live Dashboard — `dashboard.html`

**Purpose:** Show the most recent scheduler reading: aggregate consumption, per-appliance breakdown, and 24-hour history.
**Primary action:** Passive — read the numbers. No user input required.
**Auto-refresh:** Every 15 minutes via `setInterval`.

**Layout (top to bottom):**
- Nav bar (sticky)
- Hero card (full-width):
  - Predicted Wh (hero, teal, large)
  - Predicted kWh (secondary)
  - Estimated cost GBP (large, bold)
  - Last updated timestamp
- Appliance breakdown grid (9 tiles, 2-column mobile / 3-column desktop):
  - Fridge, Chest Freezer, Upright Freezer, Tumble Dryer, Washing Machine, Dishwasher, Computer, Television, Electric Heater
  - Each tile: appliance name + Wh value
- 24-hour history section:
  - Line chart: x=time, y=predicted Wh. Peak point highlighted red.
- Recent readings table: last 10 rows — time, Wh, kWh, Cost (GBP)

**Data sources:**
- Latest prediction: `GET /api/v1/predictions?tier=full&limit=1`
- Appliance values: per-appliance columns on the prediction row (`fridge_wh`, `chest_freezer_wh`, etc.)
- History chart: `GET /api/v1/predictions?tier=full&since=[24h ago]&limit=96`
- History table: `GET /api/v1/predictions?tier=full&limit=10`

**States:**

| State | Trigger | Behaviour |
|---|---|---|
| Loading | Page load | Hero card shows skeleton (animate-pulse) |
| Populated | Data fetched | All sections filled |
| Empty | No scheduler readings yet | Hero card: "No predictions found. Wait for the next scheduled reading." |
| Error | API fetch failed | Error banner shown: "Failed to load dashboard data. Please try again." |
| Auto-refresh error | setInterval fetch failed | Banner: "Auto-refresh failed. Showing last known data." Previous data stays visible. |

**Interactions:**
- Page load → fetch latest prediction → populate hero card and appliance grid
- After page load → fetch history chart and table
- Every 15 min → `refreshDashboard()`: re-fetch latest prediction, update hero and appliance grid

**Accessibility:**
- `h1`: "Current Reading"
- Appliance tiles each have a meaningful label (appliance name visible as `<p>`)
- Status banner uses `role="alert"` implied by `hidden` toggle
- Chart has visible empty-state message for screen readers

**Responsive:**
- Mobile: Hero card stacked (Wh / kWh / cost / time in 2×2 grid). Appliance grid 2-column.
- Desktop: Hero card 4-column horizontal. Appliance grid 3-column.

---

### 7.2 Forecast — `forecast.html`

**Purpose:** Show a 24-hour hourly forecast and 7-day daily forecast with weekly GBP bill projection. Optionally display model leaderboard.
**Primary action:** Click "Get Forecast" button.

**Layout (top to bottom):**
- Nav bar (sticky)
- Form card: `h1` "Energy Forecast" + "Get Forecast" button
- Error message (hidden until fetch failure)
- 24-hour forecast section (hidden until loaded):
  - Area chart: x=hour, y=predicted Wh, confidence band (yhat_lower/yhat_upper). Peak hour point amber.
- 7-day forecast section (hidden until loaded):
  - Bar chart: x=day, y=predicted Wh daily. Peak day bar amber.
- Weekly bill card (hidden until loaded):
  - Three GBP values side-by-side: Optimistic (green) / Most Likely (indigo, largest) / Pessimistic (red)
  - Caption: "Based on your 7-day consumption forecast"
- Model performance section (hidden until leaderboard loads; expandable):
  - "Forecast models (MAPE)" table — model name, MAPE, winner checkmark

**Data sources:**
- 24h forecast: `GET /api/v1/forecast/24h`
- 7d forecast: `GET /api/v1/forecast/7d` (includes `projected_week_bill`)
- Leaderboard: `GET /api/v1/models/leaderboard` (loaded on DOMContentLoaded)

**States:**

| State | Trigger | Behaviour |
|---|---|---|
| Empty | Page load | Form visible, charts hidden. No location input needed. |
| Loading | Button clicked | Button disabled, spinner visible, chart sections hidden |
| Populated | Both fetches succeed | All sections revealed |
| Error | Either fetch fails | Inline error below button; charts stay hidden |
| Partial (24h ok, 7d fails) | 7d fetch errors | Error shown; 24h section still shown |
| Leaderboard unavailable | 503 from /leaderboard | Model performance section stays hidden silently |

**Interactions:**
- "Get Forecast" click → fetch 24h and 7d in parallel → render charts → render bill card
- Chart hover/tap → tooltip with Wh and GBP cost for that hour/day
- "Model performance" heading click → toggles `model-perf-body` visibility

**Validation:**
- No input to validate — forecast endpoints take no parameters.

**Accessibility:**
- Both charts have labelled axes
- Bill card values distinguish scenario by both colour and label text (not colour alone)
- Model performance table has visible column headers

**Responsive:**
- Mobile: Charts full-width, stacked. Bill card 3-column (values smaller).
- Desktop: Charts full-width. Bill card 3-column, centred.

---

## 8. Component Library

### 8.1 NavBar
**Anatomy:** Logo left ("Diagonally Energy") + nav links right (Dashboard · Forecast)
**States:** Default / active link (teal text + 2px teal underline) / hamburger-open
**Specs:** 56px height desktop, 52px mobile. Sticky.

### 8.2 HeroCard
**Purpose:** Aggregate prediction display on `dashboard.html`.
**Anatomy:** Wh (large, indigo) · kWh (secondary) · Cost GBP (large, green) · Timestamp (small, gray)
**States:** skeleton (animate-pulse) / populated

### 8.3 ApplianceTile
**Purpose:** One appliance reading in the breakdown grid.
**Anatomy:** Appliance name (label, gray) + Wh value (indigo, semibold) + "Wh" unit
**Missing data state:** Value shows "—"

### 8.4 AreaChart (24h)
**Lib:** Chart.js 4 via CDN
**Spec:** Line (indigo `#6366f1`, 2px stroke) + confidence band (indigo 12% opacity fill between upper and lower datasets). Peak hour point amber `#f59e0b`, 6px radius. Y-axis: Wh. X-axis: hour labels.

### 8.5 BarChart (7d)
**Lib:** Chart.js 4 via CDN
**Spec:** Bars indigo `#6366f1`. Peak day bar amber `#f59e0b`. X-axis: 3-letter day names. Y-axis: Wh.

### 8.6 BillProjectionCard
**Anatomy (3 columns):** Optimistic GBP (green bg) · Most likely GBP (indigo bg, ring, largest font) · Pessimistic GBP (red bg)
**Note:** All values in GBP with `£` prefix, 2 decimal places.

### 8.7 InlineError
**Anatomy:** Error text (red) shown below triggering element
**States:** hidden / visible

### 8.8 SkeletonCard
**Spec:** Background `#F3F4F6`, shimmer animation (1.5s loop). Disabled when `prefers-reduced-motion: reduce`.

---

## 9. Design Tokens

### Colors
```
Brand
  primary:         #0D9488  (teal-600)
  primary-hover:   #0F766E  (teal-700)

Neutral
  bg:              #FFFFFF
  bg-elevated:     #F9FAFB
  surface:         #F3F4F6
  border:          #E5E7EB
  text:            #111827
  text-secondary:  #374151
  text-tertiary:   #6B7280

Semantic
  success:         #16A34A
  warning:         #F59E0B   (peak highlight)
  error:           #EF4444
  accent:          #6366f1   (chart/indigo)
```

### Typography
```
Font: Inter, -apple-system, system-ui, sans-serif
Scale: 12px (xs) · 13px (sm) · 15px (base) · 18px (lg) · 24px (2xl) · 36px (3xl) · 48px (4xl)
Weights: 400 regular · 500 medium · 600 semibold · 700 bold
```

### Spacing (4px base)
`4 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 48 · 64 · 80`

### Breakpoints
- Mobile: < 768px
- Tablet: 768–1023px
- Desktop: ≥ 1024px (max content width 1200px, centred)

---

## 10. Accessibility

- **WCAG target:** AA across all screens.
- **Contrast:** Body text `#111827` on white = 16.75:1. Indigo `#6366f1` on white = 4.7:1 (check at small sizes).
- **Touch targets:** All buttons and nav links minimum 44px height.
- **Focus indicator:** 2px solid teal outline, 2px offset, visible on all interactive elements.
- **Reduced motion:** Skeleton shimmer replaced with static color. Chart animations disabled.
- **Screen reader:** Dynamic content (hero card update on refresh) announced via `aria-live="polite"`. Errors via `aria-live="assertive"`.
- **Keyboard:** Full Tab traversal. Enter submits forecast form.

---

## 11. Motion

- **Skeleton shimmer:** 1500ms loop. Disabled with `prefers-reduced-motion`.
- **Chart render:** draws left-to-right 400ms on first load. Reduced motion: instant.
- **Error message:** fade in 100ms.
- **Nav hamburger:** dropdown 150ms slide. Closes 100ms.

---

## 12. State Coverage Matrix

| Screen | Empty | Loading | Error | Partial | Populated | Auth | Offline |
|---|---|---|---|---|---|---|---|
| dashboard.html | ✅ §7.1 | ✅ §7.1 | ✅ §7.1 | N/A | ✅ §7.1 | N/A | ✅ §7.1 |
| forecast.html | ✅ §7.2 | ✅ §7.2 | ✅ §7.2 | ✅ §7.2 | ✅ §7.2 | N/A | N/A |

---

## 13. Open Questions

| # | Question | Owner |
|---|---|---|
| 1 | Chart.js 4 via CDN chosen as charting library. Is a lighter alternative preferred? | User |
| 2 | Dashboard shows most recent scheduler reading — if scheduler is paused for a long time, data will be stale. Add a staleness warning (e.g. if last updated > 1 hour ago)? | User |
| 3 | Model performance section always loads silently if leaderboard file is missing (503). Should there be a visible message directing the user to run training? | User |

---

*End of spec — v2.0 · 2 screens*
