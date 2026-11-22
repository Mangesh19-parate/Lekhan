# DESIGN.md: Lekhan visual and interaction system

> **Upstream reference:** generated with `npx getdesign@latest add starbucks` (kept unmodified at `docs/reference/starbucks-DESIGN.upstream.md`). This file is the **project adaptation**. If the two disagree, **this file wins**.
> **Agents:** read this before writing any UI. Use tokens, never raw hex values.

---

## 0. How we use the Starbucks reference (and where we do not)

The reference describes a **retail marketing site**: hero bands, a floating "Frap" order button, gift-card photography, gold Rewards ceremony. Lekhan is a **dense, bilingual, form-heavy professional tool** used for hours at a desk. So we borrow the *feel*, not the layout.

| Borrow | Adapt | Drop |
|---|---|---|
| Warm cream canvas instead of cold white | Dense forms, tables, repeaters | Hero bands, marketing sections |
| Four-tier green system mapped to roles | Map greens to app states (primary, hover, dark surface, tint) | Floating circular order button |
| Rounded geometry (12px cards, pill buttons) | Pill for primary actions only; 8px radius on inputs | Gift-card / photo surfaces |
| Gold reserved for ceremony | Gold only for "Legally approved" | Rewards serif, Careers script fonts |
| Weight (not size) carries hierarchy | Same idea, with Devanagari-safe rules | Proprietary SoDoSans |
| `scale(0.95)` press micro-interaction | Keep, honour `prefers-reduced-motion` | Footer gold-on-green band |

### 0.1 Brand and licence cautions
- **Do not** use the Starbucks name, logo, siren, imagery, or the proprietary SoDoSans font. The palette and spacing are used as an *inspiration theme* only.
- Name tokens **neutrally** (`--brand-600`, not `--starbucks-green`) so a rebrand is a one-file change.
- Confirm with the company that a green, café-inspired look is acceptable for a legal product. A conservative alternative is the same structure with a navy brand ramp; only the token file changes.

---

## 1. Principles

1. **Calm and legible.** Law-office users need confidence, not delight. Whitespace separates, borders rarely do.
2. **Marathi first, English equal.** Every screen is designed and tested in Marathi *and* English. Marathi strings are usually longer; layouts must not break.
3. **Status is never colour alone.** Every state has an icon and a text label.
4. **Never imply legal validity.** The UI says "Draft", "Reviewed", "Approved by <role>"; it never says "valid" or "verified".
5. **Forms are the product.** Optimise for speed of data entry: keyboard-first, predictable tab order, autosave, inline errors.
6. **Desktop first.** Primary target 1280-1920 px laptops/monitors. Tablet usable. Phones: read-only history and downloads.

---

## 2. Design tokens

### 2.1 Colour (CSS variables, light theme only in v1)

```css
:root {
  /* Brand greens (reference: Starbucks / Accent / House / Uplift / Light) */
  --brand-600: #006241;   /* headings accent, brand moments */
  --brand-500: #00754A;   /* primary filled buttons, links, focus accents */
  --brand-900: #1E3932;   /* dark surfaces: nav, footer, feature panels */
  --brand-800: #2B5148;   /* dark hover / decorative */
  --brand-100: #D4E9E2;   /* tints: valid field, selected row */

  /* Ceremony */
  --approved-500: #CBA258;  /* ONLY for "Approved by <role>" seal and badge */
  --approved-100: #FAF6EE;

  /* Surfaces */
  --surface-canvas: #F2F0EB;  /* page background (warm cream) */
  --surface-sunken: #EDEBE9;  /* zone separators, table header */
  --surface-card:   #FFFFFF;
  --surface-quiet:  #F9F9F9;  /* dropdowns, form wraps */

  /* Text */
  --text-primary:   rgba(0,0,0,0.87);
  --text-secondary: rgba(0,0,0,0.58);
  --text-on-dark:   #FFFFFF;
  --text-on-dark-2: rgba(255,255,255,0.70);

  /* Semantic */
  --danger-600: #C82014;
  --danger-tint: hsl(4 82% 43% / 5%);
  --warning-500: #FBBC05;       /* advisory rule warnings; pair with dark text */
  --success-tint: hsl(160 32% 87% / 33%);

  /* Lines and focus */
  --line-subtle: rgba(0,0,0,0.12);
  --focus-ring: 0 0 0 3px rgba(0,117,74,0.35);
}
```

**Contrast (verify with a checker before release):** white on `--brand-500` is roughly 5.8:1 and on `--brand-600` roughly 7.4:1 (both pass AA for normal text). `--text-secondary` on `--surface-canvas` is roughly 5:1. `--warning-500` fails as text on white; use it only as a fill with `--text-primary` on top.

### 2.2 Typography

| Role | Latin | Devanagari (Marathi/Hindi) |
|---|---|---|
| UI font | **Inter** (substitute for SoDoSans, per the reference) | **Noto Sans Devanagari** |
| Document preview font | n/a | The template's own font (Noto Serif Devanagari or Mangal; see ARCHITECTURE.md) |
| Monospace (IDs, JSON) | JetBrains Mono | n/a |

```css
:root { --font-ui: "Inter", "Noto Sans Devanagari", "Helvetica Neue", Arial, sans-serif; }
body { font-family: var(--font-ui); color: var(--text-primary); letter-spacing: -0.01em; }

/* CRITICAL: negative tracking breaks Devanagari conjuncts. */
:lang(mr), :lang(hi) { letter-spacing: 0; line-height: 1.65; }
```

| Token | Size / weight | Use |
|---|---|---|
| `text-display` | 32 / 600, lh 1.25 | Page titles |
| `text-h1` | 24 / 600, lh 1.4, colour `--brand-600` | Section headings |
| `text-h2` | 20 / 600 | Card titles |
| `text-body` | 16 / 400, lh 1.5 (1.65 for Devanagari) | Default |
| `text-small` | 14 / 400-600 | Labels, table cells, buttons |
| `text-micro` | 13 / 400 | Helper text, captions |

Rules:
- **Weight carries hierarchy, not size jumps** (H1 and H2 can share a size; weight and colour differ), as in the reference.
- **Never** apply letter-spacing, `text-transform: uppercase`, italics for emphasis, or `font-variant` tricks to Devanagari.
- Never truncate Devanagari with CSS ellipsis mid-conjunct in data tables; wrap, or truncate with the grapheme-aware helper (`truncateGraphemes()`).
- Use Western digits by default; Devanagari digits only where a template setting asks for them.

### 2.3 Spacing, radius, elevation

| Token | Value | Use |
|---|---|---|
| `--space-1..9` | 4, 8, 16, 24, 32, 40, 48, 56, 64 px | Same scale as the reference (rem-based, 1rem = 16px in our app) |
| `--radius-input` | 8px | Inputs, selects, chips |
| `--radius-card` | 12px | Cards, dialogs, panels |
| `--radius-pill` | 50px | Primary/secondary buttons only |
| `--shadow-card` | `0 0 0.5px rgba(0,0,0,.14), 0 1px 1px rgba(0,0,0,.24)` | Default card |
| `--shadow-nav` | `0 1px 3px rgba(0,0,0,.10), 0 2px 2px rgba(0,0,0,.06)` | Top bar |
| `--shadow-dialog` | `0 8px 12px rgba(0,0,0,.14), 0 0 6px rgba(0,0,0,.24)` | Modals only |

Gutters: 16px mobile, 24px tablet, 40px desktop. Max content width 1440px; form column max 720px; two-column form+preview layout at 1280px and above.

---

## 3. Layout

```
+------------------------------------------------------------------+
| TopBar (brand-900): logo | tenant | UI language | user menu       |
+----------+-------------------------------------------------------+
| SideNav  |  PageHeader: title, breadcrumbs, primary action       |
| (cream)  |  --------------------------------------------------   |
| Wizard   |  Content (canvas bg, white cards)                     |
| History  |                                                       |
| Parties  |                                                       |
| Templates|                                                       |
+----------+-------------------------------------------------------+
```

Document wizard page: left stepper (3 steps), centre form (720px), right collapsible **Summary/Warnings** panel (320px).

---

## 4. Components

### 4.1 Buttons
| Variant | Style | Use |
|---|---|---|
| Primary | bg `--brand-500`, white text, pill, 7px 16px padding, weight 600, 40px height | One per view (Generate, Save) |
| Secondary | transparent, 1px `--brand-500` border, `--brand-500` text, pill | Back, Cancel |
| Tertiary | text only, `--brand-500` | Inline actions |
| Danger | bg `--danger-600`, white, pill | Delete, Retire template (confirm dialog required) |
Press: `transform: scale(0.95)` for 80ms; disabled at 40% opacity; loading shows spinner **and** keeps width. Disable motion when `prefers-reduced-motion`.

### 4.2 Inputs and forms
- Label above input, 14px/600. Required marker is text ("required" / "आवश्यक"), not just `*`.
- Input: 40px height, 8px radius, 1px `--line-subtle` border; focus = `--focus-ring`.
- Valid field tint `--success-tint`; invalid `--danger-tint` plus red message with an icon **below** the field, in the UI language of the user.
- Helper text 13px secondary colour. Input masks for amounts (Indian grouping), dates (dd/mm/yyyy), PAN (uppercase), pincode.
- **Dual-script fields:** names and addresses show tabs/side-by-side inputs for Marathi / English with a clear "required for this document" indicator on the active language. A "Suggest transliteration" link fills the other script as a **suggestion** that the user must confirm.
- Amount fields show the generated amount in words live under the input (read-only, in the document language).

### 4.3 RepeaterGroup (parties, installments, witnesses, boundaries)
Card per item with header "Seller 1", drag handle, duplicate, remove. Min/max enforced with disabled add/remove and helper text. Add button is secondary-pill. Keyboard: `Ctrl+Enter` adds a row, `Alt+Backspace` removes the focused row (with undo toast).

### 4.4 Status chips (colour + icon + label)
| State | Chip |
|---|---|
| Template: Draft | Outline, grey, pencil icon |
| Template: Under review | `--warning-500` fill, dark text, clock icon |
| Template: **Approved** | `--approved-100` fill, `--approved-500` border, seal icon, label "Approved by <role>" |
| Template: Retired | Grey fill, archive icon |
| Document: Draft / Reviewed / Finalised | Outline / `--brand-100` / `--brand-600` fill |
| Job: Queued / Running / Failed | Grey / `--brand-100` with spinner / `--danger-600` |
Gold (`--approved-500`) is used **nowhere else**.

### 4.5 Banners and warnings
- **Advisory warning** (non-blocking): yellow stripe, text from lawyer-authored rules, dismissible per document, recorded in audit.
- **Legal disclaimer strip** on every generated-document screen: "Generated draft. Must be reviewed by a qualified professional before execution or registration." (Marathi and English strings in the i18n file; wording to be approved by the company's lawyer.)
- **Leftover-data warning:** red tint banner listing detected names/IDs that do not belong to the current matter.

### 4.6 Data tables (history, parties, templates)
Sticky header on `--surface-sunken`, 48px rows, zebra off, row hover `--brand-100` at 40%, column sort, cursor pagination, empty state with illustration-free text and primary action. Search box debounced 250ms.

### 4.7 Document preview
Left: structured form. Right: preview pane showing the **HTML rendering of the generated text** (not a PDF), with the legal font, page-like white sheet on the cream canvas, page-break markers. Preview is labelled "Preview. The downloaded DOCX is the master."

### 4.8 Dialogs, toasts, empty states
- Dialog: 12px radius, `--shadow-dialog`, focus trapped, ESC closes, destructive confirm requires typing the document number for finalised documents.
- Toasts bottom-left, 5s, with Undo where reversible. Errors persist until dismissed and include a **correlation ID** copy button.
- Empty states: one sentence + one action. No decorative art.

### 4.9 Navigation
Top bar `--brand-900` with `--text-on-dark`. Side nav on cream, active item `--brand-100` with a 3px `--brand-600` left bar. UI language switcher (English / मराठी) always visible; Hindi UI appears later.

---

## 5. Internationalisation rules for UI
- All strings from i18n files (`en.json`, `mr.json`, later `hi.json`). No hard-coded text in components.
- Test every screen with Marathi strings (about 20-40% longer). No fixed-width buttons or labels.
- Plurals and counts via ICU message format, not string concatenation.
- Dates and numbers via `Intl` with explicit locale (`mr-IN`, `en-IN`), digits setting respected.
- **UI language and document language are separate controls**; never infer one from the other.

---

## 6. Accessibility
- WCAG 2.2 AA target. Visible focus on every interactive element. Min target 40px (44px on touch).
- Form errors announced via `aria-live`; fields linked with `aria-describedby`.
- Stepper and repeaters operable by keyboard; skip-to-content link.
- Do not rely on colour for status; icons and text always present.
- Screen-reader labels in the UI language; `lang` attribute set per element where script differs.

---

## 7. Responsive behaviour
| Width | Layout |
|---|---|
| >= 1280 | Side nav + form + summary panel |
| 768-1279 | Side nav collapses to icons; summary panel becomes a drawer |
| < 768 | Single column; wizard allowed but data-heavy forms show a "Best on a larger screen" note; history and downloads fully usable |

---

## 8. Do and don't
**Do:** use tokens; keep one primary button per view; show amount-in-words live; show who approved a template; test in Marathi.
**Don't:** use gold outside "Approved"; apply letter-spacing to Devanagari; use pure-black text; hide status in colour only; use modal-on-modal; show a PDF preview as if it were the master document; copy Starbucks logos, imagery or fonts.

---

## 9. Tailwind mapping (`frontend/tailwind.config.ts` excerpt)

```ts
export default {
  theme: {
    extend: {
      colors: {
        brand: { 100: "var(--brand-100)", 500: "var(--brand-500)", 600: "var(--brand-600)", 800: "var(--brand-800)", 900: "var(--brand-900)" },
        approved: { 100: "var(--approved-100)", 500: "var(--approved-500)" },
        canvas: "var(--surface-canvas)", sunken: "var(--surface-sunken)", card: "var(--surface-card)",
        danger: "var(--danger-600)", warning: "var(--warning-500)",
      },
      borderRadius: { input: "8px", card: "12px", pill: "50px" },
      boxShadow: { card: "var(--shadow-card)", nav: "var(--shadow-nav)", dialog: "var(--shadow-dialog)" },
      fontFamily: { ui: ["Inter", "Noto Sans Devanagari", "Helvetica Neue", "Arial", "sans-serif"] },
    },
  },
};
```

---

## 10. Agent prompt guide (quick reference)
- Primary button: `bg-brand-500 text-white rounded-pill h-10 px-4 font-semibold active:scale-95`
- Card: `bg-card rounded-card shadow-card p-4`
- Page: `bg-canvas min-h-screen`
- Approved chip: `bg-approved-100 border border-approved-500 text-text-primary` with seal icon and role label
- Devanagari text block: `lang="mr"` attribute, no tracking classes
- When unsure, read `docs/reference/starbucks-DESIGN.upstream.md` section 4 (components) and then adapt using sections 0 and 4 of this file.
