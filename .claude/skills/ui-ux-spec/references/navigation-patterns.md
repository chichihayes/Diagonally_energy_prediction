# Navigation Patterns Reference

Deep reference for choosing and specifying navigation paradigms. Most AI-built apps fail on navigation — be explicit and use this as the source of truth when designing the navigation section.

## Choosing a Primary Navigation Paradigm

### Bottom Tab Bar (mobile)
- **When to use:** 3–5 top-level destinations that users switch between frequently
- **Strengths:** Always visible, thumb-reachable, fast switching, learned pattern
- **Weaknesses:** Limited to ~5 items, eats vertical space, mixed with home indicator on iOS
- **Examples:** Instagram, Twitter/X, Spotify, Slack
- **Rules:**
  - 3–5 tabs max; if you need more, you have an IA problem, not a tab problem
  - Each tab is a parallel root, not a step in a flow
  - Active tab indicated by both color and label (color alone isn't accessible)
  - Tabs persist across screens within their stack (don't hide on level 2+ unless keyboard is open)
  - Tapping the active tab scrolls the current screen to top OR pops the stack to root
  - Never animate the tab bar itself when switching tabs

### Left Sidebar (desktop / tablet)
- **When to use:** 4+ top-level destinations on desktop; productivity tools; admin panels
- **Strengths:** Room for more destinations, can show nested structure, allows labels
- **Weaknesses:** Takes horizontal space; can be collapsed for more canvas
- **Examples:** Linear, Notion, Slack, GitHub
- **Rules:**
  - Provide a collapse toggle for users who want more canvas
  - Active item indicated by background highlight + accent stripe
  - Nested items shown via indentation, expandable/collapsible
  - Sidebar items reach Level 1 destinations; nested items reach Level 2
  - Don't put more than 8 visible items at root; group others under collapsible sections

### Top Navigation Bar
- **When to use:** Content-heavy sites, marketing pages, e-commerce
- **Strengths:** Brand-prominent, familiar from the web
- **Weaknesses:** Doesn't scale to many items; not as fast for switching as tabs
- **Examples:** Most marketing sites, Stripe Dashboard
- **Rules:**
  - Logo on left, primary nav center or left, user/account on right
  - Sticky on scroll to remain reachable
  - On mobile, collapse to hamburger or convert to bottom tab bar (prefer the latter)

### Drawer / Hamburger
- **When to use:** Sparingly. Mostly for low-priority destinations behind a primary nav.
- **Strengths:** Hides clutter
- **Weaknesses:** Out of sight, out of mind. Lower engagement. Anti-pattern as the primary nav.
- **Rules:**
  - Never the primary nav on mobile if you have 5 or fewer destinations
  - Acceptable for secondary destinations (Settings, Help, About, Sign out)
  - Open from a hamburger icon top-left or via swipe-from-edge gesture

### Hub-and-Spoke (no persistent nav)
- **When to use:** Apps with one clear job, where each task is a discrete trip back to home
- **Strengths:** Minimalist, focused
- **Weaknesses:** Slow switching between sections
- **Examples:** Most utility apps (calculator, weather), iOS Settings
- **Rules:**
  - Home screen has clear entry points to every flow
  - Every flow returns to home via back button or explicit "Done"

### Command Palette (Cmd+K)
- **When to use:** Power-user products; complement to visual nav, not replacement
- **Strengths:** Fast for keyboard users, scales to any number of actions
- **Weaknesses:** Hidden from new users; discoverability is hard
- **Examples:** Linear, Raycast, GitHub, VS Code
- **Rules:**
  - Always pair with visible navigation for discoverability
  - Show keyboard shortcut hints in the visual UI to teach the shortcut
  - Recently used items at top

## Back Behavior

The single most common navigation bug is "back doesn't go where I expect."

### Rules

1. **Back goes to the previous screen in the user's actual journey, not the IA parent.**
   - If a user arrives at ItemDetail from Search, back goes to Search.
   - If they arrive from Home, back goes to Home.

2. **Back from a tab's root does what the platform expects:**
   - iOS: nothing (or close the app — system handles this)
   - Android: previous tab in the user's switch history, then close
   - Web: browser back (handled by routing)

3. **Back from a deep link entry point:**
   - If the user landed via deep link with no previous app history, "back" should go to a sensible parent (Home), not exit the app.
   - State this explicitly in the spec for every deep-linkable screen.

4. **Back from a modal:** dismisses the modal, returns to underlying screen with state preserved.

5. **Back after a destructive or one-way action:** decide consciously. After delete, back probably shouldn't return to the deleted item's screen. After signup, back shouldn't return to the signup flow.

6. **Browser back on web:** must match in-app back. If your in-app back goes somewhere different from browser back, you have a bug.

## Tab Switching

### Rules

1. **Switching tabs is lateral**, not a navigation push. No back arrow between tabs.

2. **Each tab maintains its own stack.** Switching to a tab restores that tab's last screen and scroll position.

3. **Tapping the active tab:**
   - First tap: scroll the current screen to top
   - Second tap (when already at top): pop the stack to the tab's root
   - This is the iOS convention; web users may not know it, so don't rely on it as the only way to reset

4. **Don't reset tabs on tab switch unless explicitly desired.** Settings should remember scroll position when the user comes back from the Inbox tab.

## Modal Hierarchy

### Levels of overlay

1. **Toast** — non-blocking, transient (2–5s), bottom of screen. For notifications.
2. **Snackbar** — non-blocking, transient with optional action. For "Undo" patterns.
3. **Banner** — non-blocking, persistent until dismissed. For environmental info ("You're offline").
4. **Bottom sheet** — partial-screen modal from the bottom on mobile. For selection or short tasks. Dismissible by swipe-down or tap-outside.
5. **Action sheet** — bottom-anchored list of actions. iOS pattern for context menus.
6. **Modal (alert)** — centered, blocking, requires explicit dismissal. For confirmations.
7. **Modal (dialog)** — larger centered modal for short focused tasks (≤3 inputs).
8. **Full-screen modal** — covers everything, has its own close button. For multi-step focused flows like onboarding.

### Stacking rules

- Avoid stacking modals (modal on top of modal). If a confirmation is needed inside a modal, prefer in-place state change.
- Toasts can appear over modals.
- Banners stay underneath modals.

## Deep Links

Every screen that can be reached via URL is a potential deep link entry point. Each one needs:

1. **URL pattern:** `/items/:id`
2. **Auth requirement:** Yes/no
3. **Behavior if not authed:** show sign-in, return to deep link after
4. **Behavior if the resource doesn't exist:** 404 screen with "Take me home" CTA
5. **Behavior if the resource exists but user lacks permission:** "You don't have access to this" with sign-in-as-different-user option
6. **Back behavior from a deep-link entry:** go to a sensible parent, not exit the app

## Onboarding & First-Run Navigation

### Rules

1. **Make the onboarding skippable** unless legally required (age, terms).
2. **Save progress** — don't reset onboarding if the user closes the app halfway through.
3. **End onboarding at a "first task" screen**, not a generic empty home.
4. **Don't gate the app behind onboarding** — let users explore, surface onboarding as a banner or prompt later.

## Cross-Flow Handoffs

When a user moves between major flows, navigation must not lose context.

### Examples

- User in Settings → taps notification for new message → opens Conversation in Inbox tab → tapping back should return to Inbox root, not Settings. Notification tap is a context switch.
- User in Compose → leaves to check a reference in another tab → returns to Compose tab → composing draft must be preserved.
- User starts in Home → opens ItemDetail → opens an embedded link → web view opens. Closing web view returns to ItemDetail. Back from ItemDetail returns to Home.

### Rule

If a user can interrupt their own flow with an app-level action, that flow must persist its state. Specify which flows persist and which don't in section 6.5 of the spec.

## Anti-Patterns to Reject

These appear constantly in AI-generated UIs and should never make it past spec review:

1. **Tabs that scroll horizontally** — if you need scrolling tabs, you have the wrong nav pattern; use a sidebar or restructure
2. **Hidden primary actions** — primary CTA buried behind a menu
3. **Modals for navigation** — pushing modals as a way to "go to another section"
4. **Inconsistent back placement** — back button on the left here, right there, in the header here, in the body there
5. **Tab labels that aren't nouns** — tabs are destinations, so labels are nouns; "Home", "Search", "Inbox" not "Browsing", "Searching"
6. **Mystery icons without labels** — every nav icon needs a label, at least under it
7. **Sticky footers crowded with actions** — pick one primary action, not three
8. **Floating action buttons that block content** — FABs are acceptable for one clear action but should never sit over critical content
9. **Modals on top of modals on top of modals** — IA failure
10. **Different navigation per screen** — primary nav should be consistent across all level-1 screens

## Mobile-Specific Patterns

### Edge swipe back (iOS)
Swiping from the left edge goes back. Don't override.

### Pull to refresh
Standard on list/feed screens. Don't add an explicit refresh button if pull-to-refresh works.

### Swipe-to-delete / swipe actions
Use for inline actions on list items. Always provide a non-swipe alternative for accessibility.

### Keyboard avoidance
When the keyboard appears, the input being edited must remain visible. Adjust scroll, push content up.

## Web-Specific Patterns

### URL structure
- Use real URLs for every screen
- Use query params for filter/sort state
- Use fragments for in-page anchors
- Avoid hash-based routing unless required by hosting

### Browser controls
- Browser back/forward must work
- Refresh must reload the current state, not reset to home
- Tab title reflects current screen
- Open-in-new-tab works for any clickable thing that goes somewhere

### Hover states
Hover is desktop-only — don't rely on it for any critical information or action. Always have a touch-friendly equivalent.

## Search Navigation

### Patterns

1. **Inline search field** — always visible at the top of a list. Use for screens where search is the primary mode.
2. **Search icon → search screen** — tap an icon to push a dedicated search screen. Use for global search.
3. **Command palette** — Cmd+K for power users. Layer on top of either of the above.

### Rules

- Search history shown when search is empty (top 5 recent)
- Type-ahead suggestions update on every keystroke (debounced 150ms)
- Empty results show "No results for [query]" with suggestions
- Results show the matched term highlighted
- Clearing the query returns to the empty state, not closing search
- Pressing Escape (web) or back (mobile) exits search to the previous screen

## Notification Navigation

Every notification, when tapped, must:

1. Open the app to the relevant screen (not just home)
2. Set a sensible back stack so back goes somewhere reasonable
3. Mark the relevant item as read
4. Work whether the app is launched from cold or already open in another tab/screen

Specify the notification → screen mapping in §6.10 of the spec.
