# Component Patterns

Tailwind + vanilla CSS patterns for common components used in prototypes. Match these to the spec's component library §9.

## Button

```html
<!-- Primary -->
<button class="btn-primary">Save changes</button>

<!-- Secondary -->
<button class="btn-secondary">Cancel</button>

<!-- Destructive -->
<button class="btn-primary" style="background: var(--color-error);">Delete</button>

<!-- With loading state -->
<button class="btn-primary" :disabled="loading">
  <span x-show="!loading">Save</span>
  <span x-show="loading">
    <svg class="animate-spin" width="16" height="16">...</svg>
  </span>
</button>

<!-- Icon button -->
<button style="background: none; border: none; padding: 8px; cursor: pointer; min-width: 44px; min-height: 44px;">
  <svg width="20" height="20">...</svg>
</button>
```

## Input

```html
<div style="margin-bottom: 16px;">
  <label style="display: block; font-size: 14px; font-weight: 500; margin-bottom: 6px;">
    Email
  </label>
  <input
    type="email"
    x-model="email"
    placeholder="you@example.com"
    style="
      width: 100%;
      padding: 12px 16px;
      border: 1px solid var(--color-border);
      border-radius: var(--radius-md);
      font-size: 16px;
      background: var(--color-bg);
      color: var(--color-text);
      min-height: 44px;
    "
  />
  <div x-show="error" style="color: var(--color-error); font-size: 13px; margin-top: 4px;">
    That email's already in use.
  </div>
</div>
```

## Card

```html
<div style="
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 16px;
  box-shadow: var(--shadow-sm);
">
  <h3 style="font-size: 16px; font-weight: 600; margin: 0 0 8px;">Card title</h3>
  <p style="color: var(--color-text-secondary); margin: 0 0 12px; font-size: 14px;">Body text.</p>
  <button class="btn-secondary">Action</button>
</div>
```

## List item

```html
<div class="list-item" @click="navigate(`/item/${item.id}`)">
  <img :src="item.avatar" alt="" style="width: 48px; height: 48px; border-radius: 50%;" />
  <div style="flex: 1; min-width: 0;">
    <div style="font-weight: 500; font-size: 15px;" x-text="item.title"></div>
    <div style="
      font-size: 14px;
      color: var(--color-text-secondary);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    " x-text="item.subtitle"></div>
  </div>
  <div style="font-size: 12px; color: var(--color-text-tertiary);" x-text="item.timestamp"></div>
</div>
```

## Empty state

```html
<div style="padding: 64px 24px; text-align: center;">
  <div style="font-size: 56px; margin-bottom: 16px;">📭</div>
  <h2 style="font-size: 20px; margin: 0 0 8px;">Nothing here yet</h2>
  <p style="color: var(--color-text-secondary); margin: 0 0 24px; font-size: 15px;">
    Add your first item to get started.
  </p>
  <button class="btn-primary">Add item</button>
</div>
```

## Loading skeleton

```html
<div style="padding: 16px;">
  <template x-for="i in 6">
    <div style="display: flex; gap: 12px; margin-bottom: 16px;">
      <div class="skeleton" style="width: 48px; height: 48px; border-radius: 50%;"></div>
      <div style="flex: 1;">
        <div class="skeleton" style="height: 14px; width: 65%; margin-bottom: 8px;"></div>
        <div class="skeleton" style="height: 12px; width: 92%;"></div>
      </div>
    </div>
  </template>
</div>
```

## Error state

```html
<div style="padding: 64px 24px; text-align: center;">
  <div style="font-size: 56px; margin-bottom: 16px;">⚠️</div>
  <h2 style="font-size: 20px; margin: 0 0 8px;">Couldn't load</h2>
  <p style="color: var(--color-text-secondary); margin: 0 0 24px; font-size: 15px;">
    Check your connection and try again.
  </p>
  <button class="btn-primary" @click="forcedState = null">Retry</button>
</div>
```

## Modal (confirm)

```html
<template x-if="modal?.type === 'confirm-delete'">
  <div class="modal-backdrop" @click.self="closeModal()">
    <div class="modal">
      <h3 style="margin: 0 0 8px;">Delete this conversation?</h3>
      <p style="color: var(--color-text-secondary); margin: 0 0 24px;">
        This can't be undone.
      </p>
      <div style="display: flex; gap: 8px; justify-content: flex-end;">
        <button class="btn-secondary" @click="closeModal()">Cancel</button>
        <button class="btn-primary" style="background: var(--color-error);"
                @click="confirmDelete(modal.props.id); closeModal()">
          Delete
        </button>
      </div>
    </div>
  </div>
</template>
```

## Bottom sheet

```html
<template x-if="sheet?.type === 'filters'">
  <div class="sheet-backdrop" @click.self="closeSheet()">
    <div class="sheet">
      <!-- Drag handle -->
      <div style="width: 36px; height: 4px; background: var(--color-border-strong);
                  border-radius: 2px; margin: 0 auto 16px;"></div>
      <h3 style="margin: 0 0 16px;">Filters</h3>
      <!-- Filter options -->
      <div style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px;">
        <label style="display: flex; align-items: center; gap: 12px;">
          <input type="checkbox" /> Recent
        </label>
        <label style="display: flex; align-items: center; gap: 12px;">
          <input type="checkbox" /> Popular
        </label>
      </div>
      <button class="btn-primary" style="width: 100%;" @click="applyFilters(); closeSheet()">
        Apply filters
      </button>
    </div>
  </div>
</template>
```

## Toast

```html
<template x-if="toast">
  <div class="toast" x-text="toast"></div>
</template>
```

Triggered:
```javascript
showToast('Saved');
showToast('Couldn\'t send. Try again.', 4000);
```

## Snackbar with undo

```html
<template x-if="snackbar">
  <div style="
    position: absolute; bottom: 80px; left: 16px; right: 16px;
    background: var(--color-text); color: var(--color-bg);
    padding: 12px 16px; border-radius: var(--radius-md);
    display: flex; align-items: center; justify-content: space-between;
    box-shadow: var(--shadow-lg); z-index: 200;
  ">
    <span x-text="snackbar.message"></span>
    <button @click="snackbar.action(); snackbar = null"
            style="background: none; border: none; color: var(--color-brand-hover);
                   font-weight: 600; cursor: pointer;">
      Undo
    </button>
  </div>
</template>
```

## Tab bar

```html
<nav class="app-tabbar">
  <template x-for="tab in tabs" :key="tab.id">
    <button :class="currentTab === tab.id && 'active'" @click="tapTab(tab.id)">
      <span x-html="tab.icon"></span>
      <span x-text="tab.label"></span>
    </button>
  </template>
</nav>
```

## Header with back

```html
<header class="app-header">
  <button @click="back()" style="background: none; border: none; cursor: pointer;
                                   padding: 8px; min-width: 44px; min-height: 44px;">
    ← 
  </button>
  <h1 x-text="title" style="flex: 1; text-align: center;"></h1>
  <button style="background: none; border: none; padding: 8px; min-width: 44px; min-height: 44px;">
    ⋯
  </button>
</header>
```

## Search field (inline)

```html
<div style="padding: 12px 16px; background: var(--color-bg); border-bottom: 1px solid var(--color-border);">
  <div style="position: relative;">
    <input
      type="search"
      placeholder="Search..."
      x-model="searchQuery"
      style="
        width: 100%;
        padding: 10px 12px 10px 40px;
        background: var(--color-surface);
        border: none;
        border-radius: var(--radius-md);
        font-size: 16px;
      "
    />
    <span style="position: absolute; left: 12px; top: 50%; transform: translateY(-50%);">🔍</span>
  </div>
</div>
```

## Switch / Toggle

```html
<label style="display: flex; align-items: center; justify-content: space-between; padding: 16px; border-bottom: 1px solid var(--color-border);">
  <span>Push notifications</span>
  <input type="checkbox" x-model="pushEnabled" class="switch" />
</label>

<style>
.switch {
  appearance: none;
  width: 44px;
  height: 24px;
  background: var(--color-border-strong);
  border-radius: 12px;
  position: relative;
  cursor: pointer;
  transition: background var(--duration-fast) var(--easing-standard);
}
.switch:checked { background: var(--color-brand); }
.switch::before {
  content: '';
  position: absolute;
  top: 2px; left: 2px;
  width: 20px; height: 20px;
  background: white;
  border-radius: 50%;
  transition: transform var(--duration-fast) var(--easing-standard);
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}
.switch:checked::before { transform: translateX(20px); }
</style>
```

## Form (multi-input)

```html
<form @submit.prevent="submit()" style="padding: 24px;">
  <div style="margin-bottom: 16px;">
    <label>Name</label>
    <input type="text" x-model="form.name" />
  </div>
  <div style="margin-bottom: 16px;">
    <label>Email</label>
    <input type="email" x-model="form.email" />
  </div>
  <button type="submit" class="btn-primary" style="width: 100%;">Sign up</button>
</form>
```

## Avatar with status dot

```html
<div style="position: relative;">
  <img :src="user.avatar" style="width: 48px; height: 48px; border-radius: 50%;" />
  <div style="
    position: absolute; bottom: 0; right: 0;
    width: 12px; height: 12px;
    background: var(--color-success);
    border: 2px solid var(--color-bg);
    border-radius: 50%;
  "></div>
</div>
```

## Badge / count

```html
<span style="
  background: var(--color-error); color: white;
  font-size: 11px; font-weight: 600;
  padding: 2px 6px; border-radius: 10px;
  min-width: 18px; text-align: center; display: inline-block;
">3</span>
```

## Tag / chip

```html
<span style="
  background: var(--color-surface);
  color: var(--color-text);
  padding: 4px 10px;
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 500;
">Design</span>
```

## Progress indicator (linear)

```html
<div style="background: var(--color-surface); height: 4px; border-radius: 2px; overflow: hidden;">
  <div style="background: var(--color-brand); height: 100%; width: 60%; transition: width 300ms ease;"></div>
</div>
```

## Spinner

```html
<svg class="animate-spin" width="20" height="20" viewBox="0 0 24 24">
  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" fill="none" stroke-dasharray="40 60" />
</svg>

<style>
.animate-spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
```

## Pull-to-refresh

```html
<div style="text-align: center; padding: 8px; color: var(--color-text-secondary); font-size: 13px;"
     x-show="refreshing">
  <svg class="animate-spin" width="16" height="16">...</svg>
  Refreshing...
</div>
```

## Notes panel content (right side of shell)

When rendering the notes panel for each screen, include:
- Primary action
- Entry points
- Exit points
- All states (with current state highlighted)
- Components used
- Key interactions

This helps the user (or developer) see at a glance what the screen is supposed to do, while looking at what it actually does.
