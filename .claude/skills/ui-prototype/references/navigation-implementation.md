# Navigation Implementation Guide

How to wire up navigation in the prototype so it correctly mirrors the spec.

## Routing strategy: URL hash

Since the prototype is a single static HTML file, use URL hash routing (`#/route`) to keep it work-everywhere (file://, GitHub Pages, anywhere).

```javascript
// Read the route from hash
function parseRoute() {
  return window.location.hash.replace(/^#/, '') || '/';
}

// Listen for changes
window.addEventListener('hashchange', () => {
  app.currentRoute = parseRoute();
});

// Navigate
function navigate(route) {
  window.location.hash = route;
}
```

## Route patterns

Support both exact routes and parameterized routes:

```javascript
const routes = [
  { pattern: '/', screen: 'home' },
  { pattern: '/search', screen: 'search' },
  { pattern: '/inbox', screen: 'inbox' },
  { pattern: '/inbox/:conversationId', screen: 'conversation' },
  { pattern: '/item/:id', screen: 'itemDetail' },
  { pattern: '/profile', screen: 'profile' },
  { pattern: '/profile/settings', screen: 'settings' },
  { pattern: '/profile/settings/notifications', screen: 'notifSettings' },
];

function matchRoute(path) {
  for (const r of routes) {
    if (r.pattern === path) {
      return { screen: r.screen, params: {} };
    }
    if (r.pattern.includes(':')) {
      const regex = new RegExp(
        '^' + r.pattern.replace(/:([^/]+)/g, '(?<$1>[^/]+)') + '$'
      );
      const match = path.match(regex);
      if (match) {
        return { screen: r.screen, params: match.groups || {} };
      }
    }
  }
  return null; // 404
}
```

## Back stack

Maintain an in-memory history array. Push on navigate, pop on back.

```javascript
state.history = ['/'];

function navigate(route) {
  state.history.push(route);
  window.location.hash = route;
}

function back() {
  if (state.history.length > 1) {
    state.history.pop();
    const prev = state.history[state.history.length - 1];
    window.location.hash = prev;
  } else {
    // No history — go to sensible parent
    window.location.hash = '/';
  }
}
```

### Important: deep link back behavior

When a user lands via deep link (e.g., `prototype.html#/item/123`), the history array only contains `/item/123`. Tapping back should go to a sensible parent (typically the spec's "home" or the IA parent of the deep-link target), NOT exit.

```javascript
function init() {
  const route = parseRoute();
  if (route === '/') {
    state.history = ['/'];
  } else {
    // Deep link: prepend a sensible parent so back works
    const parent = inferParent(route);
    state.history = parent ? [parent, route] : [route];
  }
}

function inferParent(route) {
  // Match the spec's deep-link back behavior
  if (route.startsWith('/item/')) return '/';
  if (route.startsWith('/inbox/')) return '/inbox';
  if (route.startsWith('/profile/settings/')) return '/profile/settings';
  return '/';
}
```

## Tab stacks (independent histories per tab)

Each tab maintains its own stack. Switching tabs preserves the other tabs' state.

```javascript
state.tabStacks = {
  home: ['/'],
  search: ['/search'],
  inbox: ['/inbox'],
  profile: ['/profile'],
};
state.currentTab = 'home';

function switchTab(tab) {
  state.currentTab = tab;
  const stack = state.tabStacks[tab];
  const lastRoute = stack[stack.length - 1];
  window.location.hash = lastRoute;
  // Update the master history to reflect this tab's stack
  state.history = [...stack];
}

function navigate(route) {
  const screen = matchRoute(route);
  const tab = inferTabForRoute(route); // from screen registry
  if (tab && tab !== state.currentTab) {
    // Cross-tab navigation — switch tabs and replace that tab's top
    state.currentTab = tab;
    state.tabStacks[tab].push(route);
  } else if (tab) {
    state.tabStacks[tab].push(route);
  }
  state.history.push(route);
  window.location.hash = route;
}
```

### Tapping the active tab

iOS convention: first tap scrolls to top; second tap pops the tab's stack to root. Implement:

```javascript
function tapTab(tab) {
  if (state.currentTab !== tab) {
    switchTab(tab);
    return;
  }
  // Already on this tab
  if (state.tabStacks[tab].length > 1) {
    // Pop to root
    state.tabStacks[tab] = [state.tabStacks[tab][0]];
    window.location.hash = state.tabStacks[tab][0];
  } else {
    // At root — scroll to top
    document.querySelector('.device-screen').scrollTo({ top: 0, behavior: 'smooth' });
  }
}
```

## Modals

Modals are state, not routes (unless the spec specifies a routable modal). They overlay the current screen and dismiss without changing the route.

```javascript
state.modal = null;  // null or { type: 'confirm-delete', props: { itemId: '123' } }

function openModal(type, props = {}) {
  state.modal = { type, props };
}

function closeModal() {
  state.modal = null;
}

// Escape key closes modal
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && state.modal) closeModal();
});
```

Wire backdrop click to close:
```html
<div class="modal-backdrop" @click.self="closeModal()">
  <div class="modal" @click.stop>...</div>
</div>
```

## Bottom sheets

Same pattern as modals, but with the bottom-sheet animation.

```javascript
state.sheet = null;
function openSheet(type, props) { state.sheet = { type, props }; }
function closeSheet() { state.sheet = null; }
```

For mobile, allow swipe-down to dismiss. Use a simple drag handler:

```javascript
// On a sheet handle
let startY = 0;
sheet.addEventListener('touchstart', (e) => { startY = e.touches[0].clientY; });
sheet.addEventListener('touchmove', (e) => {
  const dy = e.touches[0].clientY - startY;
  if (dy > 0) sheet.style.transform = `translateY(${dy}px)`;
});
sheet.addEventListener('touchend', (e) => {
  const dy = e.changedTouches[0].clientY - startY;
  if (dy > 100) closeSheet();
  else sheet.style.transform = '';
});
```

## Toasts

Non-blocking notifications. Auto-dismiss.

```javascript
state.toast = null;
function showToast(message, duration = 2500) {
  state.toast = message;
  setTimeout(() => { state.toast = null; }, duration);
}
```

## Page transitions

Apply CSS animations on screen mount. Use Alpine's `x-transition` or a simple class:

```css
.screen-push-enter { animation: slideInRight 250ms cubic-bezier(0.2, 0, 0, 1); }
.screen-pop-enter { animation: slideInLeft 250ms cubic-bezier(0.2, 0, 0, 1); }
.tab-switch-enter { animation: fadeIn 150ms ease-out; }

@keyframes slideInRight { from { transform: translateX(100%); } to { transform: translateX(0); } }
@keyframes slideInLeft { from { transform: translateX(-100%); } to { transform: translateX(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
```

Pick the animation based on the navigation action (push, pop, switch).

## Deep link entry

When the prototype loads with a hash, jump directly to that screen and set up the back stack so back works as the spec says.

```javascript
function init() {
  const route = parseRoute();
  state.currentRoute = route;
  // Set up back stack
  const parent = inferParent(route);
  state.history = parent && parent !== route ? [parent, route] : [route];
  // Set the current tab
  const screen = matchRoute(route);
  if (screen) {
    const tab = inferTabForRoute(route);
    if (tab) {
      state.currentTab = tab;
      state.tabStacks[tab] = parent ? [parent, route] : [route];
    }
  }
}
```

## Browser back/forward

The hash change listener already handles this — when the user clicks browser back, the hash changes, the listener fires, and the prototype's `currentRoute` updates. Make sure the in-app history array stays in sync:

```javascript
window.addEventListener('hashchange', () => {
  const newRoute = parseRoute();
  // If the new route is the previous item in history, it's a back navigation
  if (state.history[state.history.length - 2] === newRoute) {
    state.history.pop();
  } else {
    state.history.push(newRoute);
  }
  state.currentRoute = newRoute;
});
```

## Keyboard shortcuts (desktop)

If the spec defines shortcuts (`/` for search, `Esc` to close, `Cmd+K`), implement them globally:

```javascript
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    if (state.modal) closeModal();
    else if (state.sheet) closeSheet();
    else back();
  }
  if (e.key === '/' && !isInputFocused()) {
    e.preventDefault();
    navigate('/search');
  }
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault();
    openCommandPalette();
  }
});
```

## Validation: navigation works

Before declaring the prototype done, manually verify:

1. Tap each tab → correct screen loads, tab bar shows active state
2. Navigate from a tab into a detail → tab bar stays, back button returns to tab
3. Switch tabs in the middle of a stack → other tab's state preserved → switch back → original tab still where you left it
4. Open a modal → close via X, backdrop, and Escape — all work
5. Open a bottom sheet (mobile) → dismiss via swipe down, tap outside, close button
6. Load with `#/item/123` → ItemDetail shows → back goes to Home, not exit
7. Browser back/forward syncs with in-app state
8. Tap active tab → scrolls to top OR pops to root
9. Toast shows, auto-dismisses
10. No console errors during any of the above
