# UI/UX Fundamentals

These are the principles the spec must reflect. They override generic best practices and personal preference when they conflict.

## 1. Navigation Hierarchy

Every screen belongs to one of four levels. The level dictates what navigation affordances exist.

- **Level 1 — Primary destinations** (3–5 max). Reachable from the persistent primary navigation (tab bar / sidebar). No "back" because they're root destinations; switching between them is lateral.
- **Level 2 — Secondary destinations**. One level deep from a primary. Has a back button. Title in the header.
- **Level 3 — Detail screens**. Two+ levels deep. Has a back button. Often a hero element at the top.
- **Modal layer** — Sits on top of any other level. Has a close (X) button rather than a back arrow. Should be dismissible by tap-outside and by swipe-down on mobile.

**Rule:** Don't build navigation that forces a user to use a back button to switch between top-level destinations. Tabs do not navigate back to each other; they switch.

## 2. The Three Wayfinding Questions

A user must be able to answer these three questions in under a second on every screen:

1. **Where am I?** — solved by clear screen title, active tab state, breadcrumb if applicable
2. **Where can I go?** — solved by visible navigation affordances and obvious primary action
3. **How do I get back?** — solved by consistent back-button placement and behavior

If any screen fails one of these, redesign it.

## 3. One Primary Action Per Screen

Every screen has exactly one most-important action. Visual hierarchy must make it obvious which one that is. If two actions feel equally important, you have two screens fighting for one slot — split them.

- Primary action: bold, filled, high-contrast button or prominent CTA
- Secondary actions: outlined or text buttons
- Tertiary actions: text links or icon buttons
- Destructive actions: never primary unless the screen exists to perform them (e.g., confirm-delete screen)

## 4. Reversibility

Every navigation action is reversible. Most destructive actions are reversible too.

- Back button always works and always returns to a sensible place
- Destructive actions show a confirmation OR show a "Undo" toast for 5+ seconds
- Form submissions that can't be undone require explicit confirmation
- Modal dismissal must not silently lose user input — confirm "Discard changes?" if there's unsaved state

## 5. State Coverage

Every screen must specify these states. Specs that only define the populated/happy-path state produce broken UIs.

- **Empty** — no data yet. Should explain what goes here and how to add it. Never just a blank screen.
- **Loading** — data is fetching. Skeleton screens for content, spinners for actions taking >1s.
- **Error** — data failed to load. Show what went wrong in plain language and a retry action.
- **Partial** — some data loaded, some failing. Show what loaded; mark what failed inline.
- **Populated / success** — the happy path.
- **Permission denied** — auth required or insufficient permissions. Link to fix it.
- **Offline** — no network. Show cached content if available; mark as stale.

## 6. Touch Targets & Hit Areas

- Mobile: minimum 44×44 pt (iOS) / 48×48 dp (Android). 8pt minimum spacing between targets.
- Web: minimum 24×24 px for desktop pointer, but 44×44 for touch-capable web.
- Visual size can be smaller than hit area — expand the hit area without expanding the visual.
- Adjacent destructive and non-destructive actions must have extra spacing.

## 7. Feedback Latency

Match feedback to expected duration:

| Action duration | Required feedback |
|---|---|
| <100ms | None needed; user perceives as instant |
| 100ms–1s | Immediate visual response (button press state, optimistic UI) |
| 1s–3s | Inline loading indicator |
| 3s–10s | Progress indicator with rough completion sense |
| >10s | Time estimate, ability to cancel, OR move to background |

Optimistic UI (showing the success state before the server confirms) is preferred for high-confidence actions (likes, follows, simple writes).

## 8. Consistency Beats Cleverness

Established patterns are established because users have learned them. Novel patterns require teaching. Pay the teaching cost only when novelty is the differentiator.

- Use platform conventions (iOS back gesture, Android up button, web browser back)
- Use familiar icons (a magnifying glass is search; don't invent a new search icon)
- Don't override system gestures (swipe-from-edge is back on iOS — don't use it for something else)

## 9. Density & Information Hierarchy

Match density to task type:

- **Action screens** (compose, settings, onboarding): spacious, one focus
- **Browse screens** (lists, feeds, libraries): balanced, comfortable scanning
- **Data screens** (tables, dashboards, analytics): denser, more per screen
- **Reading screens** (article, document): generous line height, ~65 char line length

Within any screen, establish three visual levels: primary, secondary, supporting. Anything beyond three confuses scanning.

## 10. Forms

- Labels above inputs (not placeholders-as-labels)
- Error messages inline, immediately below the field, in red with an icon
- Inline validation on blur, not on every keystroke (except for password strength meters)
- Required fields marked with `*` or "Required"; optional fields marked "Optional" — pick one, be consistent
- Smart defaults reduce input burden
- Long forms broken into steps with a progress indicator
- Auto-save where possible
- Mobile: use the correct keyboard type for each input (numeric, email, etc.)

## 11. Empty States

Every empty state is an opportunity to:
- Explain what this screen will contain once it has data
- Show the user how to get their first piece of data here
- Reinforce the product's value

Anti-pattern: blank screen with a sad icon and "No items." That's a failure.

## 12. Error Messages

Format: **What happened. Why it happened. What the user can do.**

Examples:

- ❌ "Error 500"
- ✅ "Couldn't save your changes. The connection dropped. Tap Retry."

- ❌ "Invalid input"
- ✅ "That email's already taken. Try signing in instead."

## 13. Loading

- Use skeleton screens for content-shaped loading
- Use spinners only for actions where you can't predict the shape
- Show loading immediately on user action — don't wait 200ms hoping it'll finish
- For very fast loads (<300ms), no indicator is better than a flash

## 14. Motion

Motion communicates causality. When something animates, the animation should reflect what just happened:

- Slide-in from the right: navigating forward
- Slide-out to the right: navigating back
- Fade: changing context (modals, page transitions)
- Scale up: focusing on something
- Scale down + fade: dismissing

Default durations:
- Micro (state changes, hovers): 100–150ms
- Standard (page transitions, modals): 200–300ms
- Hero (celebratory, attention-grabbing): 400–600ms

Easing:
- Standard ease for most transitions: `cubic-bezier(0.2, 0, 0, 1)` (decelerated)
- Avoid linear easing for anything other than progress bars

Respect `prefers-reduced-motion` — substitute opacity changes for motion when set.

## 15. Accessibility (WCAG AA minimum)

- Contrast: text 4.5:1, large text and UI 3:1
- Every interactive element reachable by keyboard (web) and screen reader
- Focus indicator visible at 3:1 contrast against the background
- Form fields have labels associated programmatically
- Status updates announced via ARIA live regions or platform equivalents
- Image alt text for content images; aria-hidden for decorative
- Touch targets meet minimum sizes
- Color is not the only carrier of meaning (error states need icons too)

## 16. Responsive Behavior

Don't just shrink. Restructure.

- Mobile: single column, stacked, bottom-anchored CTAs, full-bleed cards
- Tablet: 2-column where possible, side-anchored navigation
- Desktop: multi-column, sidebar navigation, hover states unlock
- Wide desktop: max content width caps (typically 1280–1440px); center with whitespace

Specify what changes at every breakpoint — don't leave it to interpretation.

## 17. Modal Discipline

Modals interrupt. Use them only when interruption is the point.

**Use a modal for:**
- Confirmation of destructive action
- A short focused task (≤3 inputs)
- Critical information requiring acknowledgment

**Don't use a modal for:**
- Navigation between sections (use routes)
- Long forms (use a route)
- Lists of options that don't fit (use a bottom sheet or new screen)
- Anything that benefits from a URL (use a route)

On mobile, prefer bottom sheets for selection and quick actions. Reserve full modals for confirmations.

## 18. Copy Voice

- Plain language. If a 12-year-old wouldn't understand it, rewrite it.
- Active voice. "We saved your changes" not "Your changes have been saved."
- Use the user's words, not internal jargon.
- Sentence case for everything except proper nouns. Avoid Title Case.
- Action button labels are verbs ("Save changes" not "OK" not "Submit").
- Empty states and errors are where voice shines — make them human.

## 19. The "Lost User" Test

For every screen, ask: if a user landed here from a deep link, with no context, would they know:
- What this screen is for
- What they can do here
- How to get to the rest of the app

If any answer is "no," the screen needs a clearer affordance.

## 20. The "First Run" Test

For every primary navigation destination, ask: what does this look like for a user with zero data? Specs that don't define this produce embarrassing first-run experiences.
