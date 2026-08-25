# Plex Console

The house style behind the CIAM deck, the Trace Walker, the review briefing and the coverage dashboard.

## Why your other machine makes ugly HTML

Nothing there tells Claude what "good" means. With no design guidance it falls back to the current
generic-AI defaults: Inter, a purple gradient hero, `rounded-lg` everywhere, emoji section markers,
everything centered — and colors declared only inside a `prefers-color-scheme` block, which is why
those pages sometimes render black text on a black ground.

The fix is not a better prompt each time. It is **writing the style down once** so every page inherits it.

## Install on the work machine

1. Copy `CLAUDE-BLOCK.md` content into that machine's `~/.claude/CLAUDE.md`
   (or the repo's `CLAUDE.md` if you only want it there).
2. Copy `base.css` into the repo that generates pages.
3. Add one line to `CLAUDE.md`:
   `Start from base.css in this repo; do not re-derive the token block.`

That's it. Every HTML file produced after that inherits the system.

## What the style actually is

| | |
|---|---|
| **Type** | IBM Plex superfamily — Serif for headings, Sans for body, Mono for data and labels |
| **Color** | Cool blue-biased neutrals, one lapis accent, and a *separate* semantic set (ok / warn / bad) |
| **Theme** | Token-based, three states: explicit light, explicit dark, unstamped system |
| **Layout** | Flex/grid with `gap`, 70ch measure, scroll wrappers on tables and diagrams |
| **Detail** | `tabular-nums`, `text-wrap: balance`, mono uppercase labels, real focus states, reduced-motion |

The single most important rule is the theming one: **every color is a token on `:root`, and no color is
ever declared only inside a media query or a `[data-theme]` block.** That one rule prevents the
unreadable-page failure entirely.

## Invoking it

Once the block is in `CLAUDE.md`, you can just say:

> build this as an HTML page

and it will follow. To be explicit:

> use the Plex Console style

## Changing the accent

Swap `--ac`, `--ac2`, `--acs` in both the light and the two dark blocks. Keep the semantic colors
where they are — if the accent starts doing double duty as a status color, status pills begin reading
as branding and the whole system loses its legibility.

## Fonts on a locked-down network

If `fonts.googleapis.com` is blocked at Northwind, drop the `<link>` entirely. The fallback stack
(Georgia / system-ui / Consolas) was chosen to hold up on its own — the page will look different but
still deliberate. Never leave a face without a fallback.
