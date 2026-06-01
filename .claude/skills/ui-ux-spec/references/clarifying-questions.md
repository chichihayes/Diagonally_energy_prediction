# Clarifying Questions Bank

Use these questions in Step 2 of the skill. Pick only the ones whose answers aren't already in the PRD. Batch them by category for readability. For each question, offer a recommended default the user can accept by saying "default."

## Platform & Form Factor

1. **Target platforms?** (mobile native, mobile web, desktop web, all of the above)
   - Default: based on PRD; if unclear, ask
2. **If mobile native: iOS, Android, or both?**
   - Default: both
3. **If web: what breakpoints?** (mobile 375px / tablet 768px / desktop 1024px / wide 1440px)
   - Default: 375 / 768 / 1024 / 1440
4. **PWA installable, or browser-only?**
   - Default: PWA installable
5. **Dark mode?** (yes / no / system-follows-OS)
   - Default: system-follows-OS

## Primary Navigation Paradigm

6. **Primary navigation for top-level destinations?**
   - Options: bottom tab bar (mobile standard), sidebar (productivity tools), top nav (content sites), drawer/hamburger (deprioritized destinations), command palette (power users)
   - Default: bottom tab bar on mobile, sidebar on desktop, with feature-specific overrides documented
7. **How many top-level destinations?**
   - Default: 3–5 (anything more than 5 needs an "overflow" pattern)
8. **Is search a top-level destination, contextual, or both?**
   - Default: both — persistent search field on relevant screens AND a global search reachable from anywhere
9. **Profile/settings access pattern?**
   - Default: avatar in top-right corner opens a menu, with full settings as a sub-screen

## User Archetypes & Primary Flows

10. **Who is the primary user?** (one-sentence persona)
11. **What does a new user do in their first session?** (the activation flow)
12. **What does a returning user do in 90% of their sessions?** (the steady-state flow)
13. **Are there secondary user types with different needs?** (admins, viewers, collaborators)
14. **What's the single most important action the app must make easy?**

## Brand & Visual Direction

15. **Existing brand guidelines?** (logo, primary color, typography) — if yes, attach or describe
16. **3 reference apps you admire and one thing you like about each.**
17. **Mood?** (playful / friendly / neutral / professional / serious / luxurious)
   - Default: friendly, modern, confident
18. **Density preference?** (spacious / balanced / dense)
   - Default: balanced — spacious for primary actions, denser for lists and data
19. **Typography preference?** (system font / specific font family / sans-serif modern / serif editorial / monospaced technical)
   - Default: Inter on web, San Francisco on iOS, Roboto on Android (system stack)
20. **Primary brand color in hex (or "pick one for me")?**
   - Default: a calm, modern blue (#2563EB) or whatever matches the product mood

## Tone & Voice

21. **Conversational or formal copy?**
   - Default: conversational but precise — short sentences, plain words, no jargon
22. **Use of emoji in microcopy?** (never / rarely / freely)
   - Default: rarely — only in empty states or celebrations
23. **First or second person?** ("You have 3 messages" vs "I have 3 messages")
   - Default: second person ("you")

## Accessibility

24. **WCAG target level?** (A / AA / AAA)
   - Default: AA (industry standard, legally safer)
25. **Must support screen readers fully?** (yes / yes-best-effort / not-priority)
   - Default: yes
26. **Must support keyboard-only navigation on web?** (yes / no)
   - Default: yes
27. **Min text size and the ability to scale up?**
   - Default: 16px base, scales to 200% without breaking layout
28. **Reduced motion support?** (respect prefers-reduced-motion)
   - Default: yes

## Performance & Offline

29. **Offline support level?** (none / read-only cached data / full offline with sync)
   - Default: read-only cached data for last-viewed screens
30. **Perceived performance priorities?** (fast first paint / instant interactivity / smooth animation)
   - Default: fast first paint with optimistic UI for common actions
31. **Skeleton screens or spinners for loading?**
   - Default: skeletons for content, spinners for actions

## Internationalization

32. **Languages to support at launch?**
   - Default: English only, but architect for i18n from day one
33. **RTL languages?** (Arabic, Hebrew)
   - Default: not at launch, but layout shouldn't preclude
34. **Locale-specific formats?** (dates, currency, numbers)
   - Default: yes, auto-detect from device

## Existing Constraints

35. **Design system already chosen?** (yes/no, which)
   - If yes: which one (Material, Tailwind UI, shadcn/ui, Radix, Chakra, custom)
36. **Component library locked in?**
   - Default: depends on framework; ask
37. **Legacy screens this needs to integrate with?**
   - If yes: describe so spec can match the existing patterns
38. **Specific anti-patterns to avoid?** (e.g. "no modals on mobile", "no horizontal scroll")

## Modal & Sheet Discipline

39. **Modal usage philosophy?** (modals for confirmations only / modals for any focused task / minimize modals)
   - Default: modals only for confirmations and short focused tasks; bottom sheets for selection on mobile; full-screen routes for anything longer than 3 fields

## Empty States

40. **Empty state philosophy?** (utilitarian / friendly / opportunistic — use empty states to teach features)
   - Default: opportunistic — every empty state teaches what to do next with a clear CTA

## Error Handling

41. **Error message philosophy?** (technical / friendly-but-honest / cheerful)
   - Default: friendly-but-honest — say what went wrong in plain language, offer the next step

## Defaults the user can confirm in bulk

If the user wants to skip detailed answers, accept "use defaults" and apply all the defaults above. Document every applied default in the spec's "Open Questions" section so the user can revisit later.
