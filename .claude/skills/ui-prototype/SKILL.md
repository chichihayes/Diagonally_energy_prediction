---
name: ui-prototype
description: Generate a fully clickable, navigable HTML prototype from a UI/UX design spec document (produced by the ui-ux-spec skill or supplied directly). The prototype renders every screen with realistic mock data, working navigation between screens (tab bar, back buttons, deep links, modals, sheets), interactive components, and all spec'd states (empty, loading, error, populated) accessible via a state-switcher overlay. Use this skill whenever the user wants to see the app before building it — phrases like "show me what this looks like", "make a prototype", "build a clickable mockup", "render the design spec", "preview the UI", or "create an HTML demo of the app". Trigger this even if the user just shares a design spec and says "build this" — produce a prototype first so they can validate before code. The output is a single self-contained HTML file with mock data that can be opened in a browser and shared.
---

# UI Prototype Generator

This skill turns a UI/UX design spec into a clickable HTML prototype. The prototype is a high-fidelity preview — it implements every screen, every state, and the full navigation graph using HTML/CSS/JS with mock data. It's not a production build; it's a way for the user to walk through the app before any real implementation begins.

## What "prototype" means here

- **Every screen from the spec is rendered.** No "TODO" screens.
- **Navigation works.** Tap a tab, navigate. Tap a back button, go back. Open a modal, dismiss it. Deep links work via URL hash.
- **Mock data is realistic.** Lorem ipsum is forbidden. Use plausible names, content, timestamps, avatars (via initials or DiceBear-style URLs), counts, etc.
- **Every state is reachable.** A state-switcher overlay lets the user view the empty, loading, error, partial, and populated state of every screen without changing data.
- **Interactions feel real.** Buttons have hover/press states, modals animate, transitions match the spec.
- **No backend.** All data is in-memory mock data; "saving" updates the in-memory store and shows a toast.

## Workflow

### Step 1 — Locate the spec

Find the UI/UX design spec. Default location: `docs/design/ui-ux-spec.md`. If the user references a different path or pastes the spec inline, use that. If no spec exists, tell the user the prototype needs a spec to build from and offer to invoke the `ui-ux-spec` skill first (which produces the spec at `docs/design/ui-ux-spec.md`).

Also read `CLAUDE.md` for any project conventions (output paths, tooling preferences) before generating.

### Step 2 — Parse the spec

Read every section. Extract:

- **Screen inventory** (§7) — the full list of screens
- **Information architecture** (§4) — the navigation tree
- **Navigation system** (§6) — tab structure, back behavior, deep links, modal rules
- **Per-screen specs** (§8) — layout, components, states, interactions
- **Component library** (§9) — reusable component definitions
- **Design tokens** (§10) — colors, typography, spacing, motion
- **Responsive behavior** (§13) — breakpoints
- **Copy & voice** (§16) — microcopy patterns for mock content

If any section is missing or thin, **make reasonable decisions and mark them in a `[PROTO ASSUMPTION]` block at the top of the prototype**. Don't stop and ask.

### Step 3 — Architect the prototype

Single file: `prototype.html` at the project root (or `docs/design/prototype.html` if the user prefers it alongside the spec — match what the project's `CLAUDE.md` suggests). Inside:

- **All HTML, CSS, JS in one file** so the user can open it locally with no build step
- **Tailwind via CDN** for utility classes (`https://cdn.tailwindcss.com`) — simplest path to spec compliance
- **Alpine.js via CDN** for reactivity (`https://unpkg.com/alpinejs`) — lightweight, no build step, declarative
- **No frameworks requiring build** (React, Vue, Svelte are excluded since they'd need bundling)
- **All design tokens defined as CSS custom properties** at `:root` so they match the spec exactly
- **One viewport frame** that simulates the target device (default: 390×844 mobile; user can toggle desktop)

Read `references/scaffold.html` for the starter structure. Read `references/mock-data-patterns.md` for what realistic mock data looks like.

### Step 4 — Build each screen

For every screen in the spec:

1. Create a `<template>` or Alpine component named for the screen
2. Implement the layout exactly as specified in §8 of the spec
3. Wire up every component from §9 of the spec
4. Wire up every interaction listed in §8 (taps, swipes, etc.)
5. Implement all states (empty/loading/error/partial/populated/auth/offline) — make them switchable via the state overlay
6. Apply the responsive behavior from §13

### Step 5 — Build the navigation system

This is the hardest part and the most-failure-prone. Get it right.

- **Routing:** use URL hash (`#/route`) so the prototype works as a static file
- **Route → screen mapping:** matches §6.4 of the spec exactly
- **Back stack:** maintain an in-memory history array; back button pops; if stack is empty, go to home
- **Tab navigation:** tapping a tab is lateral; each tab has its own back stack; switching tabs preserves the other tabs' state per §6.5
- **Modals:** open via state, dismiss via close/tap-outside/Escape, preserve underlying screen state
- **Deep links:** opening `#/item/123` lands directly on ItemDetail with no back history (back goes to Home per spec)
- **Transitions:** slide-from-right on push, slide-out-to-right on pop, fade on tab switch, scale-in on modal open — match the motion tokens in §10

Read `references/navigation-implementation.md` for full implementation patterns.

### Step 6 — Add the prototype UI shell

The prototype HTML file includes a **prototype shell** around the simulated app. The shell is not part of the app — it's the developer tools for navigating the prototype.

The shell provides:

1. **Device frame toggle** — switch between mobile / tablet / desktop viewport
2. **State switcher** — overlay buttons to view empty/loading/error/partial/populated states of the current screen
3. **Screen jumper** — dropdown to jump to any screen by name
4. **Route display** — current route shown at the top
5. **Back/forward** — prototype-level history controls (separate from in-app back)
6. **Reset button** — restart the prototype from a clean state
7. **Notes panel** — collapsible panel showing the current screen's spec excerpt for reference

Read `references/shell-template.html` for the shell scaffold.

### Step 7 — Generate mock data

Realistic mock data is critical. The user should be able to imagine the real app from the prototype.

Rules (full list in `references/mock-data-patterns.md`):

- **No Lorem ipsum.** Ever.
- **Plausible names** — use a varied set; don't repeat "John Smith"
- **Realistic content** — if the app shows messages, the messages should sound like real messages people send
- **Relative timestamps** — "2m ago", "Yesterday", "Mar 14" — distributed plausibly
- **Numbers that make sense** — follower counts, prices, ratings should look like real data
- **Avatars** — use DiceBear (`https://api.dicebear.com/7.x/avataaars/svg?seed={name}`) or color-coded initials
- **Variety** — short names AND long names, short messages AND long messages, popular items AND niche items, so layout is tested at edges

Generate 20+ items per list screen so scrolling feels real.

### Step 8 — Implement states

Every screen has a state-switcher button group in the prototype shell. Tapping a state shows that state without changing underlying data.

- **Empty:** show what's specified in the spec's empty state
- **Loading:** skeleton screens or spinners matching spec
- **Error:** error UI with retry; preserve the error indefinitely until user switches state
- **Partial:** show some loaded items + some skeletons + an inline "Some items couldn't load" banner
- **Populated:** the happy path with full mock data
- **Auth required (if applicable):** the auth-required redirect screen
- **Offline (if applicable):** offline banner + cached content

### Step 9 — Validate the prototype

Before declaring done, walk through it yourself and verify:

- [ ] Every screen from the spec inventory is reachable
- [ ] Every navigation path from §6 works
- [ ] Every state for every screen is viewable via the state switcher
- [ ] Back button works correctly from every screen including modals and deep links
- [ ] Tabs preserve state correctly per §6.5
- [ ] Deep links land correctly per §6.4
- [ ] Responsive behavior works at all breakpoints from §13
- [ ] No console errors when navigating the prototype
- [ ] Mock data is realistic and varied
- [ ] Notes panel correctly shows the current screen's spec excerpt

You can open the file in a browser to verify by running `open prototype.html` (macOS), `xdg-open prototype.html` (Linux), or `start prototype.html` (Windows) — but only do this if the user asks for verification. Otherwise just hand them the file path.

### Step 10 — Output

Save the prototype to `prototype.html` at the project root (or wherever the user specifies / where `CLAUDE.md` indicates). In the chat response, include:
1. File path
2. Screen count and state count rendered
3. Three key flows to try first (e.g., "Tap Home → tap any item → tap back; Open the state switcher and view the empty Home; Use the screen jumper to land on Settings deep")
4. Any `[PROTO ASSUMPTION]` decisions made
5. How to open it: `open prototype.html` (or platform equivalent)

## Rules

- **Self-contained.** One HTML file, no build step, runs offline in any modern browser.
- **No real backend calls.** All data is in-memory mock data.
- **Don't skip screens.** Every screen in the spec must be rendered. If a screen is mentioned but not detailed in §8, build a reasonable interpretation and mark `[PROTO ASSUMPTION]`.
- **Match the spec's design tokens exactly.** Colors, typography, spacing — copy from §10 to CSS custom properties.
- **Don't add screens not in the spec.** If something seems missing, mark it as an open question, don't invent UI.
- **Mock data must be realistic.** A prototype with bad mock data fails its purpose.
- **The state switcher must work.** Without it, the user can't see how the app behaves in non-happy paths, which is exactly where AI-built UIs fail.
- **Don't run the actual app's tests or build.** The prototype is separate from the real app code; never accidentally modify production source files in this skill.

## Reference files

- `references/scaffold.html` — the starter HTML scaffold with Tailwind + Alpine + the prototype shell
- `references/shell-template.html` — the prototype shell (device frame, state switcher, screen jumper, notes panel)
- `references/mock-data-patterns.md` — realistic mock data guide
- `references/navigation-implementation.md` — how to implement hash routing, back stack, tab stacks, modals
- `references/component-patterns.md` — Tailwind-based patterns for common components (button, card, list item, form input, modal, sheet, etc.)
