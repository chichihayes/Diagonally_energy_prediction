---
name: ui-ux-spec
description: Generate a comprehensive, production-grade UI/UX design specification document from a PRD that becomes the source of truth for an AI agent (or developer) building the app's interface. The spec covers navigation system, information architecture, screen inventory, component library, interaction patterns, accessibility, responsive behavior, motion, empty/error/loading states, and visual design tokens. Use this skill whenever the user wants to create a UI design spec, design spec, UX spec, screen spec, frontend spec, or design system document from a PRD or feature description — even if they just say "design the UI for this" or "spec out the screens". Always trigger this skill before any UI implementation begins so the resulting spec can guide construction. The skill MUST ask clarifying questions before generating the spec.
---

# UI/UX Design Spec Generator

This skill turns a PRD (or feature description) into a comprehensive, opinionated UI/UX design specification that an AI agent or developer can build from without making design decisions on their own. The output is the **source of truth for the UI**.

## Core principle

Specs that lead to good UIs are **prescriptive, not suggestive**. Every screen, component, state, transition, and interaction should be defined explicitly enough that two different developers (or two different AI agents) would build the same thing. Ambiguity in a spec becomes inconsistency in the product.

## Workflow

### Step 1 — Locate the PRD

Look for the PRD in standard project locations: `docs/prd.md`, `docs/PRD.md`, `issues/prd-*.md`, `README.md`, or any file the user references. If you can't find one, ask the user to point you to it. If no PRD exists yet, ask the user to provide one or describe the feature in enough detail that the questions in Step 2 can be answered meaningfully.

Read the PRD carefully. Extract:
- Primary user personas
- Core jobs-to-be-done
- Feature list and priorities
- Any platform constraints (mobile-only, web-only, cross-platform)
- Business goals that affect UI decisions (conversion, retention, engagement)

Also check `CLAUDE.md` and any files in `docs/` for related context (tech stack, existing patterns, decisions log) before generating the spec — the spec should align with what's already decided.

### Step 2 — Ask clarifying questions

**Do not skip this step.** Even if the PRD is thorough, the questions below surface decisions that PRDs typically leave undefined. Ask in batches grouped by category. Adapt the questions to what the PRD already answers — don't re-ask what's already specified.

Read `references/clarifying-questions.md` for the full question bank, organized by category. Ask only the questions whose answers are needed and not already in the PRD. Aim for **8–15 questions total**, batched for readability. Mark recommended defaults so the user can answer "default" to most of them. Accept "use defaults" to apply all defaults in bulk.

Categories to cover:
1. **Platform & form factor** — mobile, web, both; native vs PWA; supported breakpoints
2. **Primary navigation paradigm** — tab bar, sidebar, hub-and-spoke, command palette, etc.
3. **User archetypes & primary flows** — what does each user type do in their first session vs steady state
4. **Brand & visual direction** — existing brand, desired mood, references (apps the user admires)
5. **Density & tone** — playful vs neutral vs serious; spacious vs information-dense
6. **Accessibility commitments** — WCAG level, screen reader support, large text support
7. **Performance & offline** — offline expectations, perceived performance priorities
8. **Internationalization** — languages, RTL support, locale-specific formats
9. **Existing constraints** — design system already chosen, component library locked in, legacy screens to integrate with

### Step 3 — Apply UI/UX fundamentals

Before drafting the spec, internalize the principles in `references/uiux-fundamentals.md`. These are non-negotiable foundations the spec must reflect. Key principles include:

- **Navigation hierarchy** — every screen belongs to a level (primary, secondary, tertiary, modal) and that level dictates the navigation affordances available
- **One primary action per screen** — every screen has exactly one most-important thing; the UI must make it obvious
- **Reversibility** — every navigation action and most destructive actions are reversible (back, undo, cancel)
- **Wayfinding** — the user can always answer "where am I, where can I go, how do I get back" in under a second
- **State coverage** — every screen specifies empty, loading, error, partial, and success states; specs that omit these produce broken UIs
- **Touch targets** — minimum 44×44pt on mobile, 24×24px on web with adequate spacing
- **Feedback latency** — any action taking >100ms shows immediate feedback; >1s shows progress; >10s shows time estimate or allows cancellation
- **Consistency over cleverness** — established patterns beat novel ones unless novelty is the differentiator

### Step 4 — Generate the spec

Produce a single markdown document at `docs/design/ui-ux-spec.md` (create the `docs/design/` directory if it doesn't exist). Use the structure in `references/spec-template.md` as the skeleton — fill every section. If a section genuinely doesn't apply, write "Not applicable because…" rather than deleting it; this prevents silent omissions.

The spec MUST contain these sections in order:

1. **Document Meta** — version, date, author, status, change log
2. **Product context** — one-paragraph summary tying back to the PRD
3. **Design principles** — 3–7 product-specific principles that override generic best practices when they conflict
4. **User archetypes & primary flows** — concrete personas and their critical paths
5. **Information architecture** — site map / app map as a text tree
6. **Navigation system** — full navigation specification (see "Navigation System Spec" below)
7. **Screen inventory** — every screen, with its purpose, primary action, entry points, exits
8. **Screen specs** — one section per screen with full detail (see "Per-Screen Spec" below)
9. **Component library** — reusable components used across screens
10. **Design tokens** — colors, typography, spacing, radii, shadows, motion timings
11. **Interaction patterns** — gestures, keyboard shortcuts, focus management
12. **State coverage matrix** — table of every screen × every state (empty/loading/error/etc.)
13. **Responsive behavior** — breakpoints and what changes at each
14. **Accessibility specification** — concrete WCAG commitments with examples
15. **Motion & animation** — durations, easings, what animates and what doesn't
16. **Copy & voice** — tone guidelines, microcopy patterns, error message format
17. **Open questions** — things still undecided, with owner and target decision date

### Navigation System Spec (within section 6)

This is the most failure-prone area in AI-built apps. Be exhaustive. Include:

- **Primary navigation paradigm** chosen (tab bar / sidebar / drawer / etc.) with justification tied to user archetypes
- **Navigation hierarchy diagram** — Mermaid graph or text tree showing every screen and how they connect
- **Back behavior** — what "back" means on every screen, including from modals, sheets, and deep links
- **Deep link handling** — what URLs map to what screens; auth-required deep link behavior
- **Tab persistence** — what state persists when switching tabs (scroll position, filters, form input)
- **Modal vs sheet vs full screen decision rules** — explicit criteria for when each is used
- **Cross-flow handoffs** — how the user moves between major flows without losing context
- **Header/footer/chrome rules** — what appears on every screen and what's conditional
- **Empty-app first-run navigation** — where the user lands, what they see, where they're guided
- **Notification → screen mapping** — what each push notification opens
- **Search entry points** — where search is reachable from
- **Error route handling** — 404, expired links, auth-required redirects

### Per-Screen Spec (within section 8)

For every screen in the inventory, produce:

```
### [Screen Name]

**Route / path:** /example
**Purpose:** One sentence describing why this screen exists.
**Primary user action:** The single most important thing the user does here.
**Entry points:** How users arrive (list every path).
**Exit points:** Where users go from here (list every destination).

**Layout** (top to bottom):
- Region 1: [description, components used]
- Region 2: [description, components used]
- ...

**Components used:** Links to component library entries.

**Data shown:** Every piece of data on the screen, with source.

**States:**
- Empty: [what the user sees when there's no data]
- Loading: [skeleton? spinner? where?]
- Error: [error message, recovery action]
- Partial: [some data loaded, some failing]
- Success / populated: [the happy path]
- Permission denied / auth required: [if applicable]
- Offline: [if applicable]

**Interactions:**
- Action 1: [trigger → result, including animation]
- Action 2: ...

**Validation rules:** (for screens with input)

**Edge cases:** Long names, missing avatars, very long lists, slow networks.

**Accessibility:**
- Focus order on load
- Screen reader announcements for dynamic content
- Keyboard shortcuts (if web)
- Touch target audit

**Responsive behavior:** What changes at each breakpoint.

**Analytics events fired:** (if applicable)
```

### Step 5 — Validate the spec

Before declaring the spec complete, run through this checklist:

- [ ] Every screen in the IA has a full per-screen spec
- [ ] Every state (empty/loading/error) is specified for every screen
- [ ] Every component referenced has a definition in the component library
- [ ] Every design token referenced exists in the tokens section
- [ ] Navigation graph has no orphan screens and no dead ends
- [ ] Back behavior is defined for every screen including modals
- [ ] Deep link → screen mapping covers every screen
- [ ] Accessibility commitments are concrete (not "follow WCAG" but "every interactive element has a min 44pt target, focus visible at 3:1 contrast, etc.")
- [ ] Copy tone has at least 3 example microcopy samples
- [ ] Open questions are explicitly listed rather than glossed over

### Step 6 — Output

Save the spec to `docs/design/ui-ux-spec.md`. In the chat response, give:
1. File path
2. Word count and screen count
3. The 3 most important design decisions made in the spec (one sentence each)
4. Any open questions surfaced during generation that still need user input

Offer to update `CLAUDE.md` with a pointer to the spec so future Claude Code sessions automatically reference it as the UI source of truth.

## Rules

- **Be opinionated.** A spec full of "consider…" and "perhaps…" produces inconsistent UIs. Make decisions and document them. The user can override.
- **Be specific.** "Use friendly tone" is not a spec. "Error messages start with what went wrong in plain language, then offer the recovery action as a button. Max 80 chars for the heading, 160 for the body." is a spec.
- **Cover every state.** Specs that only cover the happy path are why apps feel broken in edge cases.
- **Make navigation explicit.** Most AI-built UIs fail on navigation. The navigation section should be the longest section.
- **Defer to platform conventions** unless there's a strong reason not to. iOS users expect iOS patterns. Web users expect web patterns.
- **Cite the PRD.** When a design decision flows from a PRD requirement, reference the requirement. This prevents drift.
- **Mark assumptions.** Anywhere you made a decision the PRD didn't explicitly support, mark it as `[ASSUMPTION]` so the user can correct it.

## Reference files

- `references/clarifying-questions.md` — the full question bank for Step 2
- `references/uiux-fundamentals.md` — the principles to apply in Step 3
- `references/spec-template.md` — the document skeleton for Step 4
- `references/navigation-patterns.md` — deep reference on navigation paradigms and when to use each
