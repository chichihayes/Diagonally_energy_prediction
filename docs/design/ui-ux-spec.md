# UI/UX Design Specification — Diagonally Energy Prediction

**Version:** 1.0
**Date:** 2026-06-01
**Status:** Draft
**Source PRD:** `issues/prd-appliance-energy-prediction.md`

## Change Log

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-06-01 | — | Initial spec — demo defaults applied |

---

## 1. Product Context

Diagonally Energy Prediction is a web-based demo that gives Nigerian homeowners a prediction of how much energy their household appliances will consume, and what that will cost at the NERC tariff rate. It serves two types of users: homeowners with Zigbee sensors who see automatic predictions every 15 minutes on a live dashboard (Smart Home tier), and homeowners with no sensors who enter two values — lights and room temperature — and receive an instant prediction (Basic tier). The UI must make numbers the hero: predictions, costs, and forecasts should be immediately readable with no navigation required. The demo has no login, no onboarding wizard, and no multi-step flows. Every page must deliver value on first load or within one tap.

---

## 2. Design Principles

1. **Numbers first, chrome last.** The predicted Wh, kWh, and NGN cost are the product. Everything else — nav, labels, inputs — is in service of those numbers. Reduce every element that is not a number or an action that produces a number.

2. **One screen, one job.** Each of the four pages does exactly one thing. The landing page routes. The simple form predicts. The dashboard shows live status. The forecast projects the future. No page tries to do two jobs.

3. **Instant or explained.** If a number is available, show it. If it is loading, show a skeleton. If it failed, say what failed and offer a retry. Never show a blank space.

4. **Mobile first, not mobile only.** The primary use case is a homeowner checking their phone. Design for 375px first. Scale up gracefully; don't just stretch the mobile layout.

5. **Teal is trust.** The brand color is used for primary actions and positive values only. Red is reserved for errors and high consumption warnings. Never use teal for errors.

---

## 3. User Archetypes & Primary Flows

### Archetype A: Basic Tier Homeowner (Amara)
- **Who:** Homeowner in Lagos, no sensors, wants to anticipate her electricity bill before it arrives
- **Primary job:** Enter lights + temperature + location → see predicted consumption and NGN cost
- **Critical path:** Land on index.html → click "Basic tier" → enter 3 values → click "Get prediction" → read result
- **Frequency:** A few times per week
- **Sophistication:** Novice — comfortable with a phone but not with energy data

### Archetype B: Smart Home Homeowner (Emeka)
- **Who:** Homeowner in Abuja with Zigbee sensors installed in all rooms
- **Primary job:** Glance at the dashboard to see current appliance consumption and cost without doing anything
- **Critical path:** Bookmark dashboard.html → open it → see latest prediction and sensor readings updated every 15 min
- **Frequency:** Daily, multiple times
- **Sophistication:** Intermediate — bought smart home kit, comfortable with data

### Cross-cutting flows

1. **First-time user activation (Amara):** Opens app → reads landing page → clicks "Try Basic tier" → enters lights=0, T1=24, location=Lagos → clicks "Get prediction" → sees "Appliances: 64 Wh (₦5.18)" — value delivered in under 60 seconds.

2. **Returning user steady state (Emeka):** Opens bookmarked dashboard.html → sees "Last updated 3 min ago" → reads predicted Wh and NGN cost → switches to forecast.html to see this week's projections → done in under 30 seconds.

3. **Forecast flow:** Either user → clicks Forecast in nav → enters or confirms location → sees 7-day area chart and monthly bill range → reads peak day callout.

---

## 4. Information Architecture

```
Root
├── index.html           — Landing: what the app does + tier selection
├── simple.html          — Basic tier: 3-input form + live result + history
├── dashboard.html       — Smart Home: live auto-updating prediction + sensor grid
└── forecast.html        — 7-day forecast chart + monthly bill projection
```

All four pages are Level 1 destinations — siblings, not parent/child. There is no concept of "back" between pages; switching is lateral via the persistent top nav. No page is gated or requires prior navigation through another page. This flat IA is correct for a demo with four discrete jobs.

---

## 5. Design Principles Reference

Applied from `references/uiux-fundamentals.md`:

- **Navigation hierarchy:** All four pages are Level 1. No Level 2+ screens exist in this demo. Modals are used only for the weather-fetch error confirmation.
- **Three wayfinding questions:** Answered by: active nav link (where am I), visible nav bar (where can I go), browser back / nav links (how do I get back).
- **One primary action per screen:** index → "Choose your tier"; simple → "Get prediction"; dashboard → none (read-only); forecast → "Get forecast".
- **Reversibility:** No destructive actions in this demo. Form inputs are always editable. No confirmation dialogs needed except weather error retry.
- **State coverage:** Specified for every screen in §8 and matrix in §12.
- **Touch targets:** All buttons and nav items minimum 44px tall on mobile.
- **Feedback latency:** Form submissions show spinner on button immediately. Forecasts show skeleton within 100ms of submit.
- **Consistency:** Nav bar identical on all four pages. Button style, spacing, and font identical throughout.
- **Density:** Form screens spacious. Dashboard and forecast denser — data is the content.

---

## 6. Navigation System

### 6.1 Primary navigation paradigm

**Top nav bar** on all pages. [ASSUMPTION: top nav is the right choice because this is a 4-page web app where all pages are peers; tab bars are for mobile-native apps; a sidebar would be overkill for 4 destinations.]

- **Desktop (≥768px):** Horizontal nav bar, full-width, sticky. Logo left. Nav links centre or right. Active page link highlighted with teal underline and teal text.
- **Mobile (<768px):** Logo left, hamburger icon (☰) right. Tapping hamburger opens a full-width dropdown menu showing all 4 nav links stacked. Tapping any link closes the menu and navigates.

Nav links (in order): **Home · Basic tier · Dashboard · Forecast**

### 6.2 Navigation hierarchy diagram

```
index.html  ←→  simple.html  ←→  dashboard.html  ←→  forecast.html
    ↑                ↑                   ↑                  ↑
    └────────────────┴───────────────────┴──────────────────┘
                         top nav bar (persistent)
```

All transitions are lateral (nav link clicks). No push/pop hierarchy exists.

### 6.3 Back behavior

| From | Back goes to |
|---|---|
| Any page via browser back | Previous page in browser history — standard browser behavior |
| Hamburger menu open | Tap outside or tap ☰ again → menu closes, stays on same page |
| Weather error toast/retry | Stays on same page, clears error state on retry |

No in-app back buttons exist. All navigation is via the persistent top nav or browser controls.

### 6.4 Deep link map

| URL | Screen | Auth required | Behavior if not authed |
|---|---|---|---|
| `index.html` | Landing | No | Show landing |
| `simple.html` | Basic tier | No | Show form (empty) |
| `dashboard.html` | Smart Home dashboard | No | Show dashboard (may show loading/no-data if scheduler hasn't run) |
| `forecast.html` | Forecast | No | Show location input, empty chart state |

No auth exists in this demo. All pages are publicly accessible.

### 6.5 Tab / page state persistence

| Page | State preserved on return via nav |
|---|---|
| simple.html | Last entered form values; last result shown — [ASSUMPTION: preserve in sessionStorage] |
| dashboard.html | Last fetched data displayed; auto-refresh continues if tab is active |
| forecast.html | Last location entered; last forecast shown |
| index.html | Always resets — it's a landing page |

### 6.6 Modal vs inline vs full-screen decision rules

This is a multi-page HTML app — there is no router. All flows are full-page navigations.

- **Inline error messages:** For form validation errors, weather fetch failures, API errors — shown immediately below the triggering element, never in a separate overlay.
- **Toast notifications:** For success confirmations (e.g. "Prediction saved") — non-blocking, bottom-right, auto-dismiss after 3 seconds.
- **No modals in this demo.** No confirmations, no dialogs. Errors are inline.

### 6.7 Cross-flow handoffs

- User reads a prediction on simple.html → clicks Forecast in nav → forecast.html should pre-fill the last-used location — [ASSUMPTION: via sessionStorage].
- User on dashboard.html → clicks Forecast in nav → forecast.html shows the dashboard's location automatically — [ASSUMPTION].
- No other cross-flow state sharing is needed for the demo.

### 6.8 Header / chrome rules

- Top nav bar appears on all four pages, identical in layout and content.
- Nav bar is sticky (fixed to top) on scroll.
- Active page link: teal text (`#0D9488`) + 2px teal underline.
- Inactive links: neutral text (`#374151`), no underline.
- On mobile, hamburger menu overlays page content with a semi-transparent backdrop.
- No footer in the demo. [ASSUMPTION]

### 6.9 First-run navigation

A new user lands on `index.html`. They see:
1. App name and one-line description
2. Two tier cards side by side (stacked on mobile): "Basic tier" and "Smart Home tier"
3. Each card has a description and a primary button: "Try Basic tier" → `simple.html`, "Open Dashboard" → `dashboard.html`
4. No onboarding wizard, no signup prompt, no cookie banner

If the user lands directly on `simple.html` with no history, they see the empty form — instructions are in the labels and placeholders.

### 6.10 Notification → screen mapping

Not applicable. This demo has no push notifications.

### 6.11 Search entry points

Not applicable. This demo has no search functionality.

### 6.12 Error routes

- **404 / page not found:** Browser shows default 404. [ASSUMPTION: not custom for demo]
- **API error (prediction):** Inline error message below submit button with Retry.
- **Weather API failure:** Inline error: "Couldn't fetch weather for [location]. Check the city name and try again." with Retry button.
- **Supabase error (history load):** Inline in the history section: "Couldn't load history. Tap to retry."

---

## 7. Screen Inventory

| # | Screen | File | Level | Primary action | Entry points | Exit points |
|---|---|---|---|---|---|---|
| 1 | Landing | `index.html` | 1 | Choose a tier | Direct URL, any nav bar "Home" click | simple.html, dashboard.html |
| 2 | Basic tier | `simple.html` | 1 | Submit prediction form | Landing CTA, nav bar | forecast.html, dashboard.html |
| 3 | Smart Home dashboard | `dashboard.html` | 1 | Read latest prediction | Landing CTA, nav bar | forecast.html, simple.html |
| 4 | Forecast | `forecast.html` | 1 | Get forecast for location | Nav bar | simple.html, dashboard.html |

---

## 8. Screen Specifications

### 8.1 Landing — `index.html`

**Route:** `index.html`
**Purpose:** Orient the user, explain the two tiers, route them to the right page.
**Primary user action:** Click a tier card CTA.
**Entry points:** Direct URL, browser bookmark, nav bar "Home" link from any page.
**Exit points:** `simple.html` (Basic tier CTA), `dashboard.html` (Smart Home CTA).

**Layout (top to bottom):**
- Nav bar (sticky)
- Hero section: App name (`h1`), one-sentence description, teal accent line
- Tier cards row (2-column desktop, 1-column mobile):
  - **Basic tier card:** Icon (lightbulb), heading "Basic tier", 2-line description, "Try Basic tier" button (primary teal)
  - **Smart Home card:** Icon (sensor/wifi), heading "Smart Home tier", 2-line description, "Open Dashboard" button (primary teal)
- How it works strip (optional, 3 steps): "Enter readings → We fetch the weather → See your predicted cost"

**Components used:** NavBar, TierCard, Button (primary), HowItWorksStrip

**Data shown:** No dynamic data — all static copy.

**States:**
- Populated (only state): Static page, no loading needed.
- Error: Not applicable — no API calls.
- Offline: Page loads from browser cache. Static content is always available.

**Interactions:**
- "Try Basic tier" button click → navigate to `simple.html` (standard `<a href>`)
- "Open Dashboard" button click → navigate to `dashboard.html`
- Nav links: navigate to respective page
- Hamburger (mobile): toggle nav dropdown

**Edge cases:**
- Very small screens (320px): cards stack, full-width buttons, no horizontal scroll.

**Accessibility:**
- `h1` is the app name.
- Tier card buttons have descriptive labels: "Try Basic tier — enter 2 values, get an instant prediction" (aria-label).
- Nav links have active state conveyed by both color and `aria-current="page"`.
- Hamburger button has `aria-expanded` and `aria-label="Open navigation menu"`.

**Responsive behavior:**
- Mobile (<768px): Hero full-width, tier cards stacked vertically, full-width buttons.
- Tablet (768–1023px): Tier cards side by side (50% each).
- Desktop (≥1024px): Tier cards side by side, max content width 1200px centered.

---

### 8.2 Basic Tier — `simple.html`

**Route:** `simple.html`
**Purpose:** Accept 3 inputs from the homeowner, return a predicted consumption and NGN cost.
**Primary user action:** Fill form and click "Get prediction".
**Entry points:** Landing CTA, nav bar "Basic tier" link, direct URL.
**Exit points:** Nav bar links (no in-page exit).

**Layout (top to bottom):**
- Nav bar (sticky)
- Page title: "Basic tier prediction" (`h1`)
- Prediction form card:
  - `lights` input — label: "Lights usage (Wh)", type=number, min=0, placeholder="0"
  - `T1` input — label: "Room temperature (°C)", type=number, step=0.1, placeholder="22.0"
  - `location` input — label: "Your city", type=text, placeholder="Lagos"
  - "Get prediction" button (primary, full-width on mobile)
- Result card (hidden until first successful response):
  - Large predicted Wh value (hero number, teal)
  - Converted kWh value (secondary)
  - Estimated cost in NGN (large, bold)
  - Weather factors section: compact grid showing T_out, RH_out, Windspeed, Visibility, Tdewpoint
- Prediction history section:
  - Section heading: "Your recent predictions"
  - Table/list: timestamp, Wh, kWh, NGN cost — most recent first, last 10 records

**Components used:** NavBar, FormCard, Input, Button (primary), ResultCard, WeatherFactors, HistoryTable, Spinner, SkeletonRow, InlineError, Toast

**Data shown:**
- Form inputs: user-entered
- Result: from `POST /api/v1/predict/simple`
- Weather factors: from API response `weather_factors`
- History: from `GET /api/v1/predictions?tier=simple&limit=10`

**States:**

- **Empty (first visit, no history):** Form visible, result card hidden. History section shows: "No predictions yet. Submit the form to get your first prediction." No table rendered.
- **Loading (form submitted):** "Get prediction" button shows spinner, label hidden, button disabled. Result card hidden or shows previous result dimmed.
- **Error (API / weather failure):** Inline error message below the button: "Couldn't get a prediction. [Reason]. Try again." with a Retry button. Previous result (if any) remains visible but is marked "Last successful result".
- **Partial (history fails, result succeeds):** Result card shows normally. History section shows inline error: "Couldn't load history." with Retry link.
- **Populated (happy path):** Result card visible with predicted Wh, kWh, NGN. Weather factors grid shown. History table updates with new row at top.
- **Offline:** Form is still fillable. On submit: inline error: "You're offline. Connect to get a prediction."

**Interactions:**
- Input blur validation: `lights` must be ≥ 0. `T1` must be a number between -20 and 60. `location` must be non-empty. Errors shown inline below each field immediately on blur.
- Submit: POST to API → show spinner → show result card on success → prepend row to history.
- Retry button: re-submits the last form values without requiring the user to re-enter.
- History loads on page load from Supabase. Skeleton rows shown during load.

**Validation rules:**
- `lights`: required, integer, ≥ 0. Error: "Enter a number of 0 or more."
- `T1`: required, float, –20 to 60. Error: "Enter a temperature between –20 and 60°C."
- `location`: required, non-empty string. Error: "Enter your city name."
- All validated on submit; individual fields also validated on blur.

**Edge cases:**
- `lights = 0` is valid — homeowner may have no lights on.
- City name not found by OWM: inline error "Couldn't find weather for '[location]'. Check the spelling."
- History table: if > 10 rows, show only 10 most recent. No pagination for demo.
- Very long city names: truncate to 40 chars in the history table.

**Accessibility:**
- Each input has an associated `<label>` (not placeholder-only).
- Inline errors use `role="alert"` and are associated with the input via `aria-describedby`.
- Result card update announced via `aria-live="polite"` region.
- "Get prediction" button disabled state communicated via `aria-disabled` and grayed appearance.
- Keyboard: Tab order follows form top-to-bottom then result then history.

**Responsive behavior:**
- Mobile: Full-width form inputs, stacked. Result card full-width. History as scrollable list cards (not table).
- Tablet+: Form card and result card side-by-side (50/50). History as table below.
- Desktop: Max 800px form container, centered.

---

### 8.3 Smart Home Dashboard — `dashboard.html`

**Route:** `dashboard.html`
**Purpose:** Show the latest auto-fetched prediction and sensor readings without requiring any input.
**Primary user action:** Read the numbers (passive — no interaction required).
**Entry points:** Landing CTA, nav bar "Dashboard" link, direct URL, browser bookmark.
**Exit points:** Nav bar links only.

**Layout (top to bottom):**
- Nav bar (sticky)
- Page title + status strip: "Smart Home Dashboard" (`h1`) + "Last updated [timestamp] · Auto-refreshes every 15 min" (secondary text, right-aligned)
- Hero prediction card (full-width):
  - Left: Predicted Wh (hero number, teal, large)
  - Center: Predicted kWh (secondary)
  - Right: Estimated cost (NGN, bold, large)
- Sensor readings grid (collapsible on mobile):
  - 9 room tiles: T1–T9 temperature + RH_1–RH_9 humidity, each showing room name, °C, and %
  - Compact, 3-column desktop / 2-column tablet / 1-column mobile
- Outside conditions strip:
  - T_out, RH_out, Windspeed, Visibility, Tdewpoint — horizontal row (scrollable on mobile)
- Prediction history section:
  - Line chart: last 24 hours of predicted Wh (x=time, y=Wh)
  - Below chart: table of last 10 predictions with timestamp and values

**Components used:** NavBar, StatusStrip, HeroPredictionCard, SensorGrid, SensorTile, WeatherStrip, LineChart, HistoryTable, Spinner, SkeletonCard, InlineError

**Data shown:**
- Latest prediction: from `GET /api/v1/predictions?tier=full&limit=1`
- Sensor readings: from the `inputs` JSONB field of the latest prediction row
- Outside conditions: from `inputs` JSONB (T_out, RH_out, Windspeed, Visibility, Tdewpoint)
- History: from `GET /api/v1/predictions?tier=full&limit=24`

**States:**

- **Empty (no predictions yet — scheduler hasn't run):** Hero card shows: "Waiting for first reading. The scheduler submits a prediction every 15 minutes. Check back shortly." Sensor grid and history hidden.
- **Loading (page load, awaiting API):** Hero card: skeleton (3 skeleton boxes). Sensor grid: skeleton tiles. History chart: skeleton rectangle.
- **Error (API fetch failed):** Hero card shows: "Couldn't load the latest prediction. [Retry]". Sensor grid shows last known values if available, faded. History shows last known chart if available.
- **Partial (history fails, latest prediction succeeds):** Hero card and sensor grid show normally. History section shows inline error with Retry.
- **Populated:** All sections filled as described in layout.
- **Offline:** Show last cached prediction with a banner: "You're offline — showing last known reading from [timestamp]."

**Interactions:**
- Page loads and immediately fetches latest prediction.
- Auto-refresh: client-side `setInterval` every 15 minutes re-fetches the latest prediction row and updates all sections without a full page reload.
- "Retry" button on error: re-fetches immediately.
- Sensor grid "expand/collapse" toggle on mobile (collapsed by default to prioritise hero card).
- History chart: hover/tap a point shows timestamp + Wh in a tooltip.

**Edge cases:**
- Scheduler has only run once (single data point): history chart shows a single point, not a line.
- Sensor readings are missing from `inputs` JSONB: sensor tile shows "—" (em dash) instead of a number.
- Timestamp "last updated": format as "3 min ago" for < 1 hour, "2 hours ago" for < 24 hours, "Yesterday at 14:32" for older.

**Accessibility:**
- Status strip "Last updated" announced via `aria-live="polite"` on auto-refresh.
- Sensor tiles: each has an `aria-label`: "Kitchen temperature: 19.9 degrees Celsius".
- Chart: table summary below chart with same data for screen readers (visually hidden with `sr-only`).
- Line chart tooltips keyboard-accessible via arrow keys.

**Responsive behavior:**
- Mobile: Hero card full-width. Sensor grid collapsed behind "Show sensor readings" toggle. History chart full-width.
- Tablet: Sensor grid 2-column, always visible.
- Desktop: Hero card + sensor grid side-by-side. History chart full-width below.

---

### 8.4 Forecast — `forecast.html`

**Route:** `forecast.html`
**Purpose:** Show a 7-day consumption forecast and projected monthly electricity bill range.
**Primary user action:** Enter location and view forecast.
**Entry points:** Nav bar "Forecast" link, direct URL.
**Exit points:** Nav bar links only.

**Layout (top to bottom):**
- Nav bar (sticky)
- Page title: "Energy forecast" (`h1`)
- Location input row: text input + "Get forecast" button (inline, side by side)
- 24-hour forecast section:
  - Section heading: "Next 24 hours"
  - Area chart: x=hour, y=predicted Wh, with confidence band (yhat_lower → yhat_upper) as shaded area
  - Peak hour callout: "Peak: [time] — [Wh]" pill badge (amber)
  - Lowest hour callout: "Lowest: [time] — [Wh]" pill badge (teal)
- 7-day forecast section:
  - Section heading: "Next 7 days"
  - Bar chart: x=day name, y=predicted Wh daily. Peak day bar highlighted amber.
  - Below chart: "Peak day: [day]  ·  Lowest day: [day]"
- Monthly bill projection card:
  - Three values side by side: Optimistic NGN / Most likely NGN / Pessimistic NGN
  - Label above each: "Best case" / "Most likely" / "Worst case"
  - Most likely value largest (hero); flanked by optimistic and pessimistic in smaller text
  - Note: "Projection based on the next 7 days extrapolated to the full month"

**Components used:** NavBar, LocationInputRow, AreaChart, PillBadge, BarChart, BillProjectionCard, Spinner, SkeletonChart, InlineError

**Data shown:**
- 24h forecast: from `GET /api/v1/forecast/24h?location=[city]`
- 7d forecast: from `GET /api/v1/forecast/7d?location=[city]`
- Bill projection: from `projected_month_bill` in the 7d response

**States:**

- **Empty (first visit, no location entered):** Location input focused. Charts area shows: "Enter your city to see your forecast." (centred, light text). Bill card hidden.
- **Loading (location submitted):** Location input and button disabled. Both charts show skeleton rectangles. Bill card shows 3 skeleton boxes.
- **Error (forecast API failure):** Inline error below the location input: "Couldn't get forecast for '[city]'. Check the city name and try again." [Retry] Charts hidden or show last result faded.
- **Error (weather failure only):** Same inline error.
- **Partial (24h succeeds, 7d fails):** 24h chart shows normally. 7d section shows inline error. Bill card hidden.
- **Populated (happy path):** All sections visible as described.
- **Offline:** Show last cached forecast with banner: "Showing forecast from [timestamp]. Connect to refresh."

**Interactions:**
- Location input: pressing Enter submits (same as clicking "Get forecast").
- On submit: fetch both 24h and 7d endpoints in parallel. Show skeletons immediately.
- Chart hover/tap: shows tooltip with exact Wh and cost values for that hour/day.
- Chart confidence band (24h): shaded area between yhat_lower and yhat_upper. Tapping the band shows "Confidence range: [lower Wh] – [upper Wh]" tooltip.
- "Retry" button on error: re-fetches with same location.
- Location pre-filled from sessionStorage if user came from another page that had a location.

**Validation rules:**
- `location`: required, non-empty. Error shown inline if submitted empty: "Enter your city name."

**Edge cases:**
- City not found by OWM: inline error "Couldn't find weather for '[city]'. Check the spelling."
- Forecast returns only 1 or 2 days: bar chart shows those bars; remaining bars hidden (not zero-filled).
- Bill projection with very high pessimistic value: ensure card doesn't overflow on mobile (truncate to 0 decimal places if > 999,999 NGN).
- Very long city name (> 30 chars): truncate in chart title and bill card note.

**Accessibility:**
- Location input has label: "City name for forecast".
- Both charts have accessible summary tables (visually hidden, `sr-only`) with the same data in tabular form.
- Chart tooltips are keyboard-accessible.
- Bill projection card values have `aria-label`: "Most likely monthly bill: 4,200 naira".

**Responsive behavior:**
- Mobile: Charts full-width, 100% height. Bill card stacks vertically (optimistic top, most likely middle, pessimistic bottom, most likely visually largest).
- Tablet: Charts full-width. Bill card 3-column horizontal.
- Desktop: 24h chart and 7d chart side by side (50/50). Bill card below, full-width, 3-column.

---

## 9. Component Library

### 9.1 NavBar

**Purpose:** Persistent top navigation on all four pages.
**Anatomy:**
- Left: Logo (app name "Diagonally" in teal + "Energy" in neutral text, 18px semibold)
- Right (desktop): Inline links — Home · Basic tier · Dashboard · Forecast
- Right (mobile): Hamburger icon (☰, 24px, 44×44 tap target)

**States:**
- Default: white background, 1px bottom border (`#E5E7EB`)
- Active link: teal text + 2px teal bottom border on the link
- Hamburger open: overlay menu full-width below nav bar, backdrop semi-transparent black 20%
- Sticky: always visible on scroll

**Specs:**
- Height: 56px desktop, 52px mobile
- Logo: left-aligned, 16px from left edge
- Links: right-aligned, 24px gap between links
- Hamburger menu: full page-width, white background, links stacked 48px each, 1px separator between

---

### 9.2 Button

**Variants:** primary, secondary, ghost, danger
**Sizes:** sm (32px height), md (40px), lg (48px)
**States:** default, hover, pressed, focus, disabled, loading

**Primary:**
- Background: `#0D9488` (teal-600)
- Hover: `#0F766E` (teal-700)
- Pressed: `#115E59` (teal-800)
- Text: white, 15px semibold
- Border radius: 8px
- Padding: 0 20px
- Loading: spinner replaces label text; button width preserved; disabled

**Secondary:**
- Background: white
- Border: 1.5px `#0D9488`
- Text: `#0D9488`, 15px semibold
- Hover: background `#F0FDFA`

**Ghost:**
- No background, no border
- Text: `#374151`, 14px medium
- Hover: background `#F3F4F6`

**Min touch target (mobile):** 44px height regardless of visual size variant.

---

### 9.3 Input

**Anatomy:** Label (above) + input field + optional helper text + optional error message (below)

**Specs:**
- Label: 14px medium, `#374151`, margin-bottom 6px
- Field: 40px height, 12px horizontal padding, border 1.5px `#D1D5DB`, border-radius 8px, font 15px
- Focus: border `#0D9488`, ring `0 0 0 3px rgba(13,148,136,0.15)`
- Error: border `#EF4444`, ring `0 0 0 3px rgba(239,68,68,0.15)`
- Error message: 13px, `#EF4444`, margin-top 4px, `role="alert"`
- Disabled: background `#F9FAFB`, text `#9CA3AF`, cursor not-allowed
- Placeholder text: `#9CA3AF`
- Mobile keyboard types: `inputmode="numeric"` for `lights` and `T1`; `inputmode="text"` for `location`

---

### 9.4 ResultCard

**Purpose:** Show the prediction output on `simple.html`.
**Anatomy (top to bottom):**
- Pill label: "Your prediction" (teal, small caps)
- Hero value: predicted Wh (36px bold, teal)
- Converted value: predicted kWh (18px, neutral)
- Cost value: "₦[amount]" (28px bold, `#111827`)
- Divider
- WeatherFactors sub-component (see 9.5)

**States:** hidden / loading (skeleton) / populated / error (shows last result faded with "Stale result" label)

---

### 9.5 WeatherFactors

**Purpose:** Show the 5 outside weather values used in the Basic tier prediction.
**Layout:** 5-column grid (3-column on mobile, wrapping)
**Each cell:** Icon + label + value
- T_out: thermometer icon, "Outside temp", "28.4°C"
- RH_out: droplet icon, "Humidity", "82%"
- Windspeed: wind icon, "Wind", "3.1 m/s"
- Visibility: eye icon, "Visibility", "10 km"
- Tdewpoint: dewdrop icon, "Dew point", "25.1°C"

---

### 9.6 SensorTile

**Purpose:** One room sensor reading in the Smart Home sensor grid.
**Anatomy:** Room label (12px, `#6B7280`) + temperature (20px bold) + humidity (14px, secondary)
**Spec:** 80px min height, 8px padding, border 1px `#E5E7EB`, border-radius 8px
**Missing data state:** Temperature shows "—", humidity shows "—"

---

### 9.7 HeroPredictionCard

**Purpose:** Primary prediction display on `dashboard.html`.
**Anatomy:**
- Left column: "Predicted consumption" label (12px) + Wh value (48px bold, teal)
- Centre: kWh value (24px, neutral)
- Right column: "Estimated cost" label (12px) + NGN value (36px bold, `#111827`)
**States:** skeleton / populated

---

### 9.8 AreaChart

**Purpose:** 24-hour forecast on `forecast.html`. Rendered with a lightweight charting library or hand-rolled SVG. [ASSUMPTION: Chart.js via CDN, consistent with no-build-step constraint.]
**Spec:**
- Line: teal `#0D9488`, 2px stroke
- Confidence band fill: teal at 15% opacity
- Y-axis: Wh values, auto-scaled, gridlines `#F3F4F6`
- X-axis: hour labels, 6-hour intervals on mobile, hourly on desktop
- Tooltip on hover/tap: white card, 1px border, showing hour, Wh, and NGN cost
- Peak hour point: amber dot `#F59E0B`, 6px radius

---

### 9.9 BarChart

**Purpose:** 7-day forecast on `forecast.html`.
**Spec:**
- Bars: teal `#0D9488`, 8px border-radius top corners
- Peak day bar: amber `#F59E0B`
- X-axis: 3-letter day abbreviations (Mon, Tue...)
- Y-axis: Wh, auto-scaled
- Tooltip: same style as AreaChart

---

### 9.10 BillProjectionCard

**Purpose:** Monthly bill range display on `forecast.html`.
**Anatomy (3 columns):**
- Left: "Best case" label + optimistic NGN (smaller)
- Centre: "Most likely" label + most likely NGN (largest, bold, teal)
- Right: "Worst case" label + pessimistic NGN (smaller)
**Note below:** "Projection based on 7-day forecast extrapolated to month" (12px, `#6B7280`)

---

### 9.11 InlineError

**Purpose:** Inline error message below a form or section.
**Anatomy:** ⚠ icon + error text + optional Retry link/button
**Spec:** 14px, `#EF4444`, `role="alert"`, `aria-live="assertive"`

---

### 9.12 Toast

**Purpose:** Non-blocking success confirmation.
**Spec:** Fixed bottom-right, 320px max width, white background, shadow-md, 8px border-radius, 3px left teal border, 3s auto-dismiss, slide-in from right 200ms, slide-out to right 200ms.
**Contents:** ✓ icon + message text (14px) + optional dismiss ×

---

### 9.13 SkeletonCard / SkeletonRow / SkeletonChart

**Purpose:** Loading placeholder for content areas.
**Spec:** Background `#F3F4F6`, shimmer animation (left-to-right gradient sweep, 1.5s loop), border-radius matches the component it replaces. Respects `prefers-reduced-motion` (no shimmer — static `#F3F4F6` if reduced motion set).

---

## 10. Design Tokens

### Colors

```
Brand
  primary:           #0D9488   (teal-600)
  primary-hover:     #0F766E   (teal-700)
  primary-pressed:   #115E59   (teal-800)
  primary-light:     #F0FDFA   (teal-50)
  primary-border:    #99F6E4   (teal-200)

Neutral
  bg:                #FFFFFF
  bg-elevated:       #F9FAFB
  surface:           #F3F4F6
  border:            #E5E7EB
  border-strong:     #D1D5DB
  text:              #111827
  text-secondary:    #374151
  text-tertiary:     #6B7280
  text-placeholder:  #9CA3AF

Semantic
  success:           #16A34A
  success-bg:        #F0FDF4
  warning:           #F59E0B
  warning-bg:        #FFFBEB
  error:             #EF4444
  error-bg:          #FEF2F2
  info:              #0D9488
```

### Typography

```
Font family: Inter, -apple-system, system-ui, sans-serif
(loaded via Tailwind CDN — system fallback if Inter not available)

Scale:
  xs:   12px / 1.4  — captions, labels
  sm:   13px / 1.4  — secondary text, table cells
  base: 15px / 1.5  — body, inputs
  lg:   18px / 1.4  — emphasized body
  xl:   20px / 1.3  — section headings
  2xl:  24px / 1.2  — page subheadings, chart axis secondary values
  3xl:  30px / 1.1  — cost values, kWh values
  4xl:  36px / 1.0  — hero Wh value (dashboard)
  5xl:  48px / 1.0  — primary dashboard hero (largest number on screen)

Weights:
  regular:  400
  medium:   500
  semibold: 600
  bold:     700
```

### Spacing (4px base)

```
1:   4px
2:   8px
3:   12px
4:   16px
5:   20px
6:   24px
8:   32px
10:  40px
12:  48px
16:  64px
20:  80px
```

### Radii

```
sm:   4px
md:   8px
lg:   12px
xl:   16px
full: 9999px
```

### Shadows

```
sm:  0 1px 2px rgba(0,0,0,0.05)
md:  0 4px 6px -1px rgba(0,0,0,0.10), 0 2px 4px -2px rgba(0,0,0,0.05)
lg:  0 10px 15px -3px rgba(0,0,0,0.10), 0 4px 6px -4px rgba(0,0,0,0.05)
```

### Motion

```
Durations:
  micro:   100ms   — hover states, button press
  fast:    150ms   — dropdown open, toast slide
  base:    200ms   — modal fade, card expand
  slow:    300ms   — page-level transitions
  shimmer: 1500ms  — skeleton loop

Easings:
  standard:   cubic-bezier(0.2, 0, 0, 1)
  decelerate: cubic-bezier(0, 0, 0.2, 1)
  accelerate: cubic-bezier(0.4, 0, 1, 1)
```

---

## 11. Interaction Patterns

### Gestures (mobile web)
- Swipe down on a long page: standard scroll
- Pull down at the top of dashboard.html: no pull-to-refresh (auto-refresh is on a timer; a manual refresh button is provided instead)
- [ASSUMPTION: no custom gesture handling needed for this demo]

### Keyboard shortcuts (web)
- `Enter` in any form input: submits the form
- `Escape`: closes hamburger menu if open

### Focus management
- On page load: focus set to `<main>` or first interactive element below the nav
- On form error: focus moves to the first field with an error
- On result card appearing: announced via `aria-live` but focus does not move (user may still want to edit the form)
- On hamburger menu open: focus trapped inside the menu; `Escape` closes and returns focus to the hamburger button

---

## 12. State Coverage Matrix

| Screen | Empty | Loading | Error | Partial | Populated | Auth req | Offline |
|---|---|---|---|---|---|---|---|
| index.html | N/A — static | N/A | N/A | N/A | ✅ §8.1 | N/A | ✅ §8.1 |
| simple.html | ✅ §8.2 | ✅ §8.2 | ✅ §8.2 | ✅ §8.2 | ✅ §8.2 | N/A | ✅ §8.2 |
| dashboard.html | ✅ §8.3 | ✅ §8.3 | ✅ §8.3 | ✅ §8.3 | ✅ §8.3 | N/A | ✅ §8.3 |
| forecast.html | ✅ §8.4 | ✅ §8.4 | ✅ §8.4 | ✅ §8.4 | ✅ §8.4 | N/A | ✅ §8.4 |

All cells are ✅ or N/A. Auth required is N/A for all screens (no auth in demo).

---

## 13. Responsive Behavior

### Breakpoints

- **Mobile:** < 768px
- **Tablet:** 768–1023px
- **Desktop:** ≥ 1024px (max content width 1200px, centered)

### What changes per breakpoint

| Aspect | Mobile | Tablet | Desktop |
|---|---|---|---|
| Nav | Hamburger dropdown | Hamburger dropdown | Inline links |
| Tier cards (index) | Stacked, full-width | Side by side, 50% each | Side by side, 40% each, centered |
| Form + result (simple) | Stacked vertically | Side by side, 50/50 | 800px max, centered |
| History (simple) | Card list | Table | Table |
| Sensor grid (dashboard) | Collapsed behind toggle, 1-col when expanded | Always visible, 2-col | Always visible, 3-col |
| Hero card (dashboard) | Stacked (Wh / kWh / NGN) | 3-column horizontal | 3-column horizontal |
| Charts (forecast) | Full-width, stacked | Full-width, stacked | Side by side, 50/50 |
| Bill card (forecast) | Stacked vertical | 3-column horizontal | 3-column horizontal |
| Button width | Full-width | Auto (content) | Auto (content) |

---

## 14. Accessibility Specification

- **WCAG target:** AA across all screens.
- **Contrast:** Body text `#111827` on white = 16.75:1 ✅. Secondary text `#374151` on white = 10.4:1 ✅. Teal `#0D9488` on white = 4.52:1 ✅ (meets AA for large text and UI). Teal on white for small body text (under 18px non-bold): [ASSUMPTION: check at implementation — consider `#0A7169` if `#0D9488` falls below 4.5:1 at small sizes].
- **Touch targets:** All buttons minimum 44px height. All nav links minimum 44px tap area. Input fields 40px visual, padded to 44px touch area.
- **Focus indicator:** 2px solid teal outline (`#0D9488`), 2px offset, visible on all interactive elements. Never removed — only moved if a design requires it, with an equivalent replacement.
- **Reduced motion:** Skeleton shimmer removed (static color). Toast slide replaced with fade. All transitions replaced with opacity-only.
- **Screen reader support:** Every interactive element has an accessible name. Dynamic content (result card, dashboard refresh) announced via `aria-live="polite"`. Errors announced via `aria-live="assertive"`.
- **Keyboard navigation:** Full Tab traversal in logical order. No keyboard traps except the hamburger menu (intentional, dismissed with Escape). Enter submits forms.
- **Text scaling:** Layout tested at 200% browser zoom — no horizontal scrolling, no clipped text.
- **Color independence:** All semantic states (error, success, warning) conveyed by icon + text + color, never color alone.

---

## 15. Motion & Animation

- **Nav hamburger:** dropdown slides down 150ms, `decelerate` easing. Closes slides up 100ms, `accelerate`.
- **Skeleton shimmer:** 1500ms loop, linear gradient sweep left to right. Disabled when `prefers-reduced-motion: reduce` (static placeholder color instead).
- **Toast:** slides in from right 150ms, waits 3s, slides out right 150ms. Reduced motion: fade in/out only.
- **Result card appear:** fade in 200ms, `decelerate`. No slide (avoids layout shift on mobile).
- **Button loading spinner:** spins 600ms loop, linear. No entrance/exit animation — swaps instantly with label.
- **Chart render:** draws in left to right over 400ms on first load. Subsequent updates (auto-refresh) update values with a 200ms opacity transition. Reduced motion: instant render, no animation.
- **Error message appear:** fade in 100ms (fast — user needs to see it immediately).

---

## 16. Copy & Voice

### Tone
Direct and plain. Numbers are the hero; words stay out of the way. Short sentences. No jargon. Second person ("your prediction", "your city"). Sentence case for everything.

### Voice rules
- State what happened, then what to do: "Couldn't fetch weather. Try a different city name."
- Never blame the user: not "You entered an invalid city" — say "We couldn't find that city."
- Currency: always "₦" prefix, always 2 decimal places for bill projections, 0 decimal places for hero values above ₦100.
- Energy: always show both Wh and kWh. Wh is the hero number (it's what the model outputs).

### Microcopy examples

**Empty states:**
- simple.html, no history: "No predictions yet. Fill in the form to get your first one."
- dashboard.html, no data: "Waiting for the first reading — the scheduler runs every 15 minutes."
- forecast.html, no location: "Enter your city to see next week's forecast."

**Loading:**
- Form button: spinner, no text change (width preserved)
- Dashboard status strip: "Refreshing…" → "Updated just now"

**Success:**
- Toast after prediction saved: "Prediction saved."

**Errors:**
- Weather fetch failure: "Couldn't fetch weather for [city]. Check the city name and try again." [Retry]
- API down: "Couldn't reach the prediction service. Try again in a moment." [Retry]
- History load failure: "Couldn't load your history." [Tap to retry]
- No OWM result: "We couldn't find '[city]' — try a nearby major city."

**Buttons:**
- "Get prediction" (not "Submit")
- "Get forecast" (not "Go")
- "Retry" (not "Try again")
- "Show sensor readings" / "Hide sensor readings" (toggle, not "Expand")

---

## 17. Open Questions

| # | Question | Owner | Target |
|---|---|---|---|
| 1 | [ASSUMPTION] Chart.js via CDN chosen as charting library. Is this acceptable, or is a lighter alternative (e.g. uPlot, ApexCharts) preferred? | User | Before implementation |
| 2 | [ASSUMPTION] sessionStorage used to persist location and last form values across page navigations. Is this acceptable, or should it be localStorage (persists across sessions)? | User | Before implementation |
| 3 | [ASSUMPTION] Teal `#0D9488` on white for interactive text (links, active nav). Needs a contrast check for body-size text (<18px, non-bold) — may need to darken to `#0A7169`. | Developer | Implementation |
| 4 | [ASSUMPTION] No custom 404 page in the demo — browser default. Acceptable for demo scope? | User | Before launch |
| 5 | [ASSUMPTION] Dashboard auto-refresh uses `setInterval` (client-side, every 15 min). No WebSocket or SSE needed for demo. Confirm. | User | Before implementation |
| 6 | [ASSUMPTION] Offline caching via `sessionStorage` only — no service worker / PWA installability for this demo. Confirm. | User | Before implementation |
| 7 | teal `#0D9488` as brand color chosen by spec author. User should confirm this aligns with any existing brand direction. | User | Before implementation |

---

*End of spec — v1.0 · 4 screens · ~3,800 words*
