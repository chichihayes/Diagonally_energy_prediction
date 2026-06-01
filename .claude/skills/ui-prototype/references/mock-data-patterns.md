# Mock Data Patterns

Realistic mock data is the difference between a prototype that helps the user see the product and one that just looks like a demo. **No Lorem ipsum, ever.**

## Core Rules

1. **Plausible.** Mock data should be indistinguishable from real data at a glance.
2. **Varied.** Edge cases matter — include short AND long names, popular AND niche items, fresh AND old timestamps.
3. **Coherent.** A messaging app's contacts shouldn't include "John Smith #4" — pick real-sounding distinct people.
4. **Localized to the product.** A fitness app's mock workouts are different from a recipe app's mock recipes. Don't recycle generic data.

## People & Names

Use a varied set across genders, cultures, and name lengths. A good starter list:

```
Maya Patel, Jordan Reyes, Aiko Tanaka, Marcus Bennett,
Priya Sharma, Diego Hernandez, Zara Ahmed, Yusuf Okonkwo,
Sophie Laurent, Hiroshi Yamamoto, Luca Romano, Amara Okafor,
Felix Andersen, Ngozi Adeyemi, Tomás Silva, Mei Chen,
Olivia Brennan, Rashid Al-Mansouri, Elena Volkov, Kwame Asante
```

For corporate mock data, include realistic-sounding company names:
```
Northwind Logistics, Stellar Health, Pinecone Studios, Bluefin Capital,
Cascade Robotics, Vermillion AI, Ironwood Books, Saltwater Coffee
```

## Avatars

Use DiceBear for consistent, free avatar generation:
```
https://api.dicebear.com/7.x/avataaars/svg?seed={name}
https://api.dicebear.com/7.x/initials/svg?seed={name}
https://api.dicebear.com/7.x/bottts/svg?seed={name}  (robot for AI/system avatars)
```

For initials-only fallback (no network):
```html
<div style="width:40px;height:40px;border-radius:20px;background:#2563EB;color:#fff;
            display:flex;align-items:center;justify-content:center;font-weight:600;">
  MP
</div>
```

Vary the initial colors by hashing the name.

## Timestamps

Show realistic distributions: recent items are minutes/hours ago, older items are days/weeks/months ago. Mix relative ("2m ago") and absolute ("Mar 14") based on age.

```javascript
function relativeTime(minutesAgo) {
  if (minutesAgo < 1) return 'just now';
  if (minutesAgo < 60) return `${minutesAgo}m`;
  if (minutesAgo < 24*60) return `${Math.floor(minutesAgo/60)}h`;
  if (minutesAgo < 7*24*60) return `${Math.floor(minutesAgo/(24*60))}d`;
  // For older, use absolute month/day
  const d = new Date(Date.now() - minutesAgo*60*1000);
  return d.toLocaleDateString('en', { month: 'short', day: 'numeric' });
}
```

Distribute timestamps across the list so the first few are very recent, middle is hours/days, end is weeks/months.

## Messages

Real messages are short, casual, often incomplete sentences. Mix lengths and content types:

```
"hey are we still on for tomorrow?"
"sent! 🎉"
"lol that's wild"
"Just got home — long day. Tomorrow works for me. Want to do 2pm?"
"can you send me the file when you get a chance"
"thanks 🙏"
"sounds good"
"📎 Q4-report-final-v3.pdf"
"I'll call you in 10"
"running late, traffic is brutal"
"Hey! I was looking over the proposal you sent and had a few thoughts. The framework looks solid but I'm not sure about the pricing assumptions in section 3. Got a minute to chat?"
```

Include a few that are clearly automated/system messages:
```
"Maya Patel added you to the project 'Q4 Planning'"
"Your subscription renews on March 14"
"Reminder: meeting in 15 minutes"
```

## Numbers, Counts, Prices

Use plausible distributions, not round numbers:

```
✅  $47.50, $129.00, $8.99, $1,247.00
❌  $50.00, $100.00, $10.00, $1,000.00

✅  1,247 followers, 23 likes, 412 views
❌  1000 followers, 50 likes, 500 views

✅  4.7 ★ (382 reviews), 4.2 ★ (8,941 reviews), 3.9 ★ (12 reviews)
❌  4.5 ★ (100 reviews), 4.5 ★ (100 reviews), 4.5 ★ (100 reviews)
```

Power-law distributions are realistic — most items have a few engagements, a small number have many.

## Lists & Feeds

For any list screen, generate **at least 20 items** so scrolling feels real. Mix:

- A few "popular" / "featured" items at top
- Several normal items in the middle
- A handful of older / niche items at the end
- One or two edge cases:
  - An item with no image (test placeholder)
  - An item with very long title (test truncation)
  - An item with an emoji in title (test font fallback)
  - An item from years ago (test old-timestamp format)

## E-commerce / Product Data

```
Names: real-sounding products, not "Product 1"
  ✅ "Linen Crew Tee — Sand"
  ✅ "Ceramic Pour-Over Dripper, 02"
  ✅ "Wool Beanie, Heather Grey"
  ❌ "Product A", "Item 123"

Prices: see numbers section
Categories: real categories from the actual niche
Reviews: vary length, voice, rating
Stock status: mix of "In stock", "Only 2 left", "Out of stock"
```

## Calendar / Schedule Data

```
✅ "Design review with the team — 30 min"
✅ "Doctor's appointment — Dr. Chen"
✅ "Lunch with Priya"
✅ "Block: deep work on Q4 plan"
❌ "Meeting 1", "Event A"
```

Distribute across the week realistically — most workdays have 3–6 events, weekends have 0–2, evenings empty for most users.

## Settings & Preferences

For settings screens, show toggles and selectors in **realistic positions**, not all on or all off:

```
Notifications: ON
  - Direct messages: ON
  - Mentions: ON
  - New followers: OFF
  - Marketing emails: OFF

Theme: System
Language: English
Time zone: America/Chicago
```

## Multi-User Conversations

For collaboration apps, show conversations with mixed participation:

```
Maya: hey just saw the v2 mocks
Maya: love the new nav!
You: thanks! still iterating on the empty states
Jordan: 👍
You: @Jordan can you take a look at the search flow when you have a min
Jordan: yeah will do by EOD
[Jordan is typing...]
```

## Empty States

When generating mock data for empty states, generate the **specific empty case**, not a generic one:

- Empty inbox: "No messages yet" + "Start a conversation" CTA
- Empty cart: "Your cart is empty" + "Browse products" CTA
- No search results: "No results for 'xyz123'" + suggestion: "Check spelling or try different keywords"

## Error Messages

Use plain language matching the spec's tone:

```
✅ "Couldn't load your messages. Check your connection."
✅ "That email's already in use. Try signing in instead."
✅ "Your card was declined. Update your payment method."

❌ "Error: HTTP 500"
❌ "Network request failed"
❌ "Invalid input"
```

## Anti-patterns

- ❌ Lorem ipsum
- ❌ Repeating names ("John Smith 1", "John Smith 2")
- ❌ All-round numbers (everyone has 100 followers, every price is $10)
- ❌ All-recent or all-old timestamps
- ❌ Identical avatar placeholders for everyone
- ❌ Sequential, predictable IDs in user-facing content ("Item 1, Item 2, Item 3")
- ❌ Bot-generated-sounding content ("This is a sample message for testing purposes")
- ❌ Single-state data (everyone is "active", every order is "pending") — vary statuses

## Quick Generation Template

```javascript
const NAMES = ['Maya Patel', 'Jordan Reyes', 'Aiko Tanaka', /* ... */];
const MESSAGE_TEMPLATES = [
  'hey are we still on for tomorrow?',
  'sent! 🎉',
  'lol that\'s wild',
  /* ... */
];

function mockUser(seed) {
  const name = NAMES[seed % NAMES.length];
  return {
    id: String(seed),
    name,
    avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(name)}`,
    handle: '@' + name.toLowerCase().replace(/\s+/g, '').slice(0, 15),
  };
}

function mockMessage(seed) {
  const user = mockUser(seed);
  const text = MESSAGE_TEMPLATES[seed % MESSAGE_TEMPLATES.length];
  // Distribute timestamps: first 3 are very recent, next 5 are hours, rest spread
  const minutesAgo = seed < 3 ? seed * 2 : seed < 8 ? seed * 30 : seed * 120;
  return { ...user, text, timestamp: relativeTime(minutesAgo) };
}

const mockFeed = Array.from({ length: 24 }, (_, i) => mockMessage(i));
```

Adapt this pattern to whatever data shape the product requires.
