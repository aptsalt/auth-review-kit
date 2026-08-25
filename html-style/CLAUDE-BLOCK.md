# Plex Console — HTML/CSS house style

> **Paste everything below the line into the `CLAUDE.md` of the machine or repo that produces ugly HTML.**
> It is written as instructions to Claude, not as documentation for you.
>
> Optional but better: also copy `base.css` next to it and add
> *"Start from `base.css` in this repo; do not re-derive the token block."*

---

## HTML & CSS house style — "Plex Console"

Any time you produce an HTML page, report, dashboard or artifact, follow this. It is not optional
styling advice; it is the house style.

### Step 0 — write the plan before the code

Before the first line of HTML, state in 3 lines:

1. **Palette** — 4–6 named hex values, and what the accent is
2. **Type** — the display face and the body face, by name
3. **Layout** — the structural idea in one sentence

Then build exactly that. Skipping this step is what produces generic output — the plan is the whole
mechanism, not a formality.

### Type

Use the **IBM Plex superfamily** in three roles, with real fallbacks:

```css
--f-display:"IBM Plex Serif",Georgia,"Times New Roman",serif;   /* headings */
--f-body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;  /* prose */
--f-mono:"IBM Plex Mono",ui-monospace,Consolas,monospace;       /* data, code, labels */
```

Load via `<link>` from `fonts.googleapis.com`. If that host is blocked on this network, drop the link —
the fallback stack is chosen to hold up alone. Never leave a face without a fallback.

Rules:
- Serif for headings, sans for body, mono for anything countable, quoted, or labelled
- Running text at **65–70ch** max (`max-width:70ch`)
- `text-wrap: balance` on every heading
- Uppercase labels get `font-size:10px; letter-spacing:.13em` and mono — never uppercase body text
- `font-variant-numeric: tabular-nums` anywhere digits sit in a column
- Set a scale and stay on it. Do not invent a fifth heading size mid-page.

### Color

- **Cool, blue-biased neutrals.** Not pure grey — a grey with a slight hue lean toward the accent reads
  as chosen rather than inherited.
- **One accent**, used sparingly. Default lapis: `#1B4F9C` light / `#79ADFF` dark.
- **Semantic colors are a separate set** — ok / warn / bad. The accent must never double as a status
  color, or a status pill reads as branding and a brand element reads as an alert.

### Theming — the rule that prevents unreadable pages

Three states exist, not two: explicit light, explicit dark, and *unstamped* (system default). Define
every color as a token in three blocks:

```css
:root { /* complete LIGHT palette — every token defined here */ }

@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]) { /* redefine ONLY the tokens */ }
}

:root[data-theme="dark"] { /* redefine the same tokens again */ }
```

Then style components **through the tokens only**.

**Never declare a color whose only definition lives inside a media query or a `[data-theme]` block.**
That is the single most common cause of an artifact rendering one theme's text on the other theme's
background. Before finishing, scan the stylesheet for any such color and hoist it.

`body` must set an explicit `background` from a token. A transparent body borrows the host's ground.

### Layout

- Sibling groups use flex or grid with `gap`. Not per-element margins — they collapse and double.
- Tables, diagrams and code blocks live in their own `overflow-x:auto` wrapper. The page body must
  never scroll sideways.
- Watch selector specificity. Type-based and element-based rules fighting over the same padding is how
  spacing silently breaks.
- Cards: `border:1px solid var(--line)`, `border-radius:10-12px`. Consistent, not per-element.

### Detail that separates finished from generated

- Visible `:focus-visible` state on everything interactive
- `@media (prefers-reduced-motion:reduce)` killing transitions and animations
- `scroll-padding-top` matching sticky header height, so anchors don't land under it
- Close every non-void element; double-quote every attribute

### Structure carries meaning

- Section numbers only when the content is genuinely a sequence
- Eyebrow/kicker labels above headings, mono and uppercase
- Status shown as **form plus value** — a pill, a chip, a severity stripe — so it reads at a glance
- A pull quote for the one idea that must survive the page

### Never do these

These are the current generic-AI defaults. Do not spend a design decision on any of them:

- Warm cream `#F4F1EA` with a serif display and a terracotta accent
- Near-black with a single acid-green or vermilion pop
- Purple-to-blue gradient hero on white
- **Inter** or **Space Grotesk** as the "safe" face
- Emoji as section markers
- Everything centered
- `rounded-lg` on every element
- An accent bar or rail on every rounded card

### Title

`<title>` is a short, specific noun phrase — two to four words — that names the page like a product.
Not a summary, not a category label, and never a name with an explainer appended after a dash or colon.

### Self-contained

Inline all CSS and JS. Embed images as data URIs. Google Fonts is the only external host that may be
referenced. Wrap every `localStorage` read and write in `try/catch` and render correctly when it throws
or returns nothing.
