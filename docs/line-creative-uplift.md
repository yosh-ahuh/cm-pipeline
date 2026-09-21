# Spot — Creative Uplift (LINE Design System, bold direction)

A **creative direction + component upgrade blueprint** for a major visual/UX lift of Spot.
Grounded in LINE's design *principles* and *exact numbers*, but bespoke to Spot: dark, indigo `#4A67E3`, **「選ぶだけ」**, gentle-partner tone, low-IT audience.

- Not a compliance catalog. The audit lives in [`line-design-reflection.md`](line-design-reflection.md) (R1–R22); this doc goes **beyond** it into concept + hero surfaces + motion.
- Numbers are pulled from the LINE PDFs and mapped to Spot tokens (`styles/tokens.css`) so an implementer never has to reopen a PDF.
- Non-breaking: every move reuses existing tokens/classes (`--accent`, `.opt`, `.proj`, `.hn-btn`, `.wiz-board`, `.empty`, `.toast`…). New pieces are additive.
- Source: `/Users/yosh/work/SPOT/LINE Design System/` (98 PDF). Target: `spot-app/index.html` + `spot-app/styles/tokens.css`.

---

## 1. Creative direction — "選ぶだけ、が気持ちいい"

Spot's whole promise is that **choosing is the work**. There is no writing, no timeline, no prompt box. So the *act of choosing* must be the most crafted, most rewarding moment in the entire product. That is the concept: **make every choice feel like pressing a big, warm, confident button — and make the app light up to say "good pick."**

Grounded in LINE's principles, tuned for Spot:

| LINE principle | Spot expression |
|---|---|
| Clear primary tasks | **One question fills the screen.** Never two decisions competing. The question is `--t-display` (32px) Bricolage; everything else recedes. |
| WE ≠ USERS | Built for a marketer who has never opened Figma. **Every screen answers "what do I tap?" in under 2 seconds.** Helper text is permanent, not a tooltip you must discover. |
| A cohesive experience | The wizard is **one continuous path with a visible spine**, not 6 disconnected forms. You always see where you are and where you're going. |
| Reliable design | **Honest feedback on every action** (LINE Feedback: ≥1 feedback per action). Nothing happens silently; nothing pretends to be done when it isn't. |
| Motion with purpose | Motion only ever means: *you chose*, *it committed*, *here it comes*. No decoration-for-decoration. |

### The three big moves

**Big move 1 — Indigo is the light, not the paint.**
Spot's stage is near-black (`--ground #131318`). Indigo should behave like **a light source in that dark room**, not a fill you splash around. One signature gesture: a soft radial indigo **aura** (`radial-gradient(circle, var(--accent), transparent 70%)`, opacity .35–.45, blurred) that appears behind (a) the hero, and (b) *whatever the user just selected*. Selecting an option literally makes the screen glow toward it. This already exists on `.hero-new::after` — **promote it to a system primitive** (`--glow`) and reuse it on selected cards, the FAB, and the result reveal.
Result: the app feels calm and premium when idle, and *alive* the instant you touch it.

**Big move 2 — Option cards are physical objects, not list rows.**
The choice cards (`.opt`) are the soul of the product, so make them **big, tactile, and unmistakably pressable**. Generous internal padding, a resting lift-shadow, a spring on hover (`--ease-spring`), and on select they **fill with indigo container + snap a checkmark** (LINE Chips: selected = ✓). Choosing is a satisfying *thunk*, not a faint highlight. See §2a for exact spec.

**Big move 3 — Every surface has a job title.**
- **Wizard** = "the guided path." A studio assistant walking you through 5 questions.
- **Home** = "your studio." Where your ads live; one obvious way to start a new one.
- **Result** = "the premiere." A finished ad is *presented*, celebrated, then quietly made downloadable.

Depth strategy (elevation ladder, dark-tuned, already in tokens):
`--ground` (stage) → `--surface-low` (rails/wells) → `--surface` (cards, +`--shadow-1`) → **hover/selected** (`--surface-2/3` + `--shadow`) → **overlays** (sheets/menus, `--shadow-lift`). Never more than one `--shadow-lift` layer on screen at once (LINE: one modal/tooltip/banner at a time).

Motion language (three verbs, from §4): **arrive** (`--ease-emphasized`, content in), **commit** (`--ease-spring`, selection), **reveal** (staged fade+lift, result). Everything respects `prefers-reduced-motion` (already wired at `index.html:788`).

---

## 2. Hero-surface redesigns

### 2a. Creation WIZARD — "選ぶだけ" made bold

Current: `.wiz-board` is a 3-column desktop grid (`180px | 1fr | 320px`) — left step nav, center options, right live summary. Options are `.opt` cards in `.opt-grid` (`minmax(160px,1fr)`). Good bones. The lift makes **choosing bigger, the path clearer, and mobile a proper bottom-sheet flow.**

**A. One question, huge.**
Keep exactly one `.step-q` per step at `--t-title-lg` today → **promote the active step's question to `--t-display` (32px)** Bricolage, with the JP helper (`.step-hint`) directly under it at `--t-body` / `--muted`. Everything else on the step is options. LINE: *make primary tasks intuitive; one screen, one task.*

**B. Bigger, bolder option cards.** (full spec in §3)
- Min card **height 96px desktop / 84px mobile**, internal padding **16px** (LINE content margin), radius `--r-md (14px)`.
- Resting state: `--surface`, `1px --line`, `--shadow-1`. Icon chip 40×40 `--r-sm`.
- Hover: lift `translateY(-3px)` + `--shadow`, border `--line-strong`, `--ease-spring` 200ms (tiny overshoot = "springy, pickable").
- **Selected: fill `color-mix(--accent-soft 55%, --surface)`, border `--accent-ink`, icon chip → solid `--accent` with `--on-accent` glyph, and a 20px checkmark tick snaps in** (top-right, `--ease-spring`). This is the "thunk." Add a faint `--glow` behind selected multi-select cards.
- Single-select (data-single): selecting one **auto-clears the rest** (LINE Choice chip); multi-select shows ✓ on each (LINE Filter chip). Show the mark, not just color — never rely on color alone (low-IT + a11y).

**C. Persistent progress — the spine.**
- **Desktop:** keep the left `.step-nav` rail but make it a true **spine**: connected nodes (the `::before` connector already exists), done = solid `--accent` check, current = ringed `box-shadow: 0 0 0 4px --accent-soft`, future = hollow `--line-strong`. Add the numeric progress you already animate (`.wiz-progress` fill).
- **Add a dot Page Indicator** under the question on all viewports (LINE Page Indicator): dots **5px inactive / 7px active**, active `--accent-ink`, inactive `--outline`, gap 8px, 12px above content. ≤5 steps = one dot each. This is the at-a-glance "how many left."
- Keep the top eyebrow progress bar (`.wiz-progress`, 4px, `--accent-ink` fill, `--dur-slow --ease-emphasized`).

**D. Footer nav — decisive.**
`.wiz-nav`: **primary "次へ" on the right** (LINE Box Button: primary right in a horizontal pair), secondary "戻る" ghost on the left, `.grow` spacer between. Primary is `.hn-btn` (indigo grad), min-height `--control-h-lg (44px)` desktop, **48px mobile** (already set at `index.html:1176`). Primary **disabled until the step is answered** (LINE: keep disabled until required input is met) — and disabled means *label dims only* (`--faint`), the button shape stays. On the final step the primary becomes **「CMをつくる」** with a `.spin` loading state on tap (see §3 buttons).

**E. Step transition = "arrive."**
Between steps, the outgoing options fade+lift out (8px, `--dur-fast`), the new question and cards **stagger in** (each card +12ms, translateY 8→0, `--dur-slow --ease-emphasized`). Reuse `.wiz-step.on { animation: fade }`; add the stagger. Direction-aware is a bonus (forward = from right, back = from left) but optional.

**F. Mobile = bottom sheet, not a cramped grid.** (LINE Bottom Sheet)
On `≤720px`, when a step has many options (formats, industries), present them in a **modal bottom sheet** instead of shrinking cards to 1-col mush:
- Top radius **14px** (LINE fixed), width **100%**, no side margin, `--surface`, `--shadow-lift`.
- **Handlebar** on top (grab affordance), header = **Close-only** (default), title left.
- Options as a **List pattern** (full-width rows, 44px min, right-side ✓) or the same `.opt` cards stacked.
- Button area **vertical, single primary** ("決定") — LINE: 3 buttons not recommended; one primary for confirmation.
- Modal type (dimmer `--scrim`, blocks background) for a required choice; sheet slides up `--dur-slow --ease-emphasized`, dimmer fades. This is the single most impactful mobile upgrade for a low-IT thumb-driven user.

### 2b. HOME / dashboard — "your studio"

Current: `.dash-hero` (`1fr | 340px`) with `.hero-new` gradient hero + a `.proj-grid` of result cards, `.empty` state. Solid. The lift: make **starting a new CM impossible to miss**, and make the video list feel like a shelf of finished work.

**A. Hero = one primary action.** (LINE: clear primary task, one primary per screen)
`.hero-new` keeps the indigo grad + `--glow` aura. Inside: eyebrow (mono, `--accent-ink`), `--t-display` headline, one line of `--muted` subcopy (max 44ch), and **exactly one** primary CTA `.hn-btn` **「新規CMをつくる」**. Remove any competing same-weight button from the hero (LINE: don't put white + indigo primaries side by side — `index.html:529` already commits to this).

**B. First-run empty state = the real hero.** (LINE Empty)
When there are zero videos, the empty state *is* the page, centered:
- Optional pictogram in an `--accent-soft` rounded tile (reuse `.empty .e-ic`, 60×60, `--r-lg`).
- Title (`--t-title`, `--ink`) + one calm description line (`--t-body-sm`, `--muted`). **No urgency/CTA-style shouting** (LINE Empty: "refrain from content that causes urgency or confusion") — voice is 頼れる相棒: *「まずは1本、いっしょに作ってみましょう。」*
- **One button** (LINE: 1 recommended, max 2): 「最初のCMをつくる」.
This doubles as the onboarding moment (memory: first-run tutorial). Pair with 1–2 coachmark Tooltips (§3) pointing at the FAB / hero.

**C. Mobile FAB — 新規CM always one thumb away.** (LINE FAB, currently absent in Spot)
On `≤720px`, a **circular FAB, 56px** (LINE spec 54pt; round up to Spot's touch target), icon area ~32px, **`+` or a spark glyph**, `--accent-grad` fill + `--glow`, `--on-accent` icon, `--shadow-lift`. **Fixed bottom-right, 16px margin** (LINE placement), above everything, sits above safe-area inset. Single-action FAB (tap → new CM wizard) — *not* an expandable menu (Spot has one creative task, so a plain FAB is correct; LINE reserves `+`-expand for multi-task). Constructive action, appears once content exists; on the empty state the centered button carries it instead.

**D. Result videos = a shelf of Cards.** (LINE Card)
`.proj-grid` stays `auto-fill minmax(255px,1fr)`, gap `--s-4`. Each `.proj`:
- **Full-bleed thumbnail on top** (the ad's key frame / first cut). Radius inherits card `--r-lg`; whole card is `overflow:hidden`.
- **Status indicator top-left, non-tappable** (LINE: indicators are info, not tap targets) — `.proj-status` pill, `rgba(12,12,18,.72)` + backdrop-blur, colored dot (制作中 = `--warn`, 完成 = `--good`).
- **Format + duration indicators bottom-corners** on the thumb (LINE Card: duration text `00:15`, media-type icon, aspect badge). Small, glassy, non-tappable.
- Body: name (`--t-body-lg`, 1 line ellipsis), meta row (`--muted`, `--t-label`) with format glyphs.
- **Whole card taps → detail/result** (LINE Card primary action = entire card). The only *supplemental* action (⋯ menu / delete) is a separate icon button, top-right, that stops propagation (LINE: supplemental action separate from card tap).
- Hover: `translateY(-3px)` + `--shadow` (already at `.proj:hover`). Loading list = **Skeleton** shimmer (`.skel`, already implemented), never a spinner over cards (LINE: don't combine skeleton + progress).

**E. Filters as Segmented/Choice, honest.**
The 制作中/完成 filters (`.filter[aria-pressed]`) = LINE Filter chips: selected shows fill + the count. Keep counts truthful (memory: honesty over inflated states).

### 2c. Video RESULT card — "the premiere"

A finished ad is the emotional payoff. Present it like the app is *proud* of it, then make the practical stuff (download) calm and secondary.

**A. Reveal, don't just render.** (LINE Feedback: Transition/Motion)
When generation completes, the result **arrives**: player scales up from 96%→100% + fades (`--ease-emphasized`, `--dur-slow`), a soft `--glow` blooms behind it once, and a single Toast confirms 「初稿ができました」 (auto-dismiss ~4s, `bg black 80%`, LINE Toast). One celebratory beat, then it settles.

**B. Player-first, full-bleed.**
The player (`.preview-area`) is the hero of this view: large, `--r-lg`, black stage, centered play affordance. **Format tabs above it** (横16:9 / 縦9:16 / 1:1, `.tab[role=tab]`) — LINE Tab: underline **2px** `--accent-ink`, states 100/70/50 opacity, one selected at a time. Switching format cross-fades the frame (`--dur`).

**C. Gradient scrim for any on-video text.** (LINE Card full-image rule)
Any label over the frame (title, duration, "AD") sits on a bottom-to-top gradient dim scrim so it's always legible — never raw text on imagery.

**D. Download = the calm secondary.**
The variants list (`.variant`, `.rx-*`) stays. Primary action of the view is **「すべてダウンロード（ZIP）」** (`.btn-primary`), but it's presented as competent, not loud — it's below the celebration, not competing with it. Per-cut download stays as small icon buttons (LINE: ≤2 right-side actions per row). If the user lacks write permission, the disabled state shows *why* in text (LINE: disabled still communicates state; already handled by `dlGuard`).

**E. Result cards in a collection = horizontal or vertical Card collection** (LINE Card placement) — vertical grid on home, optional horizontal swipe strip for "recent renders."

---

## 3. Component specs — exact numbers

All numbers are LINE-sourced, mapped to Spot tokens. Reuse existing tokens; don't invent parallel values.

### Buttons

| Property | Value | Source → Spot |
|---|---|---|
| Corner radius | **10px** (`--r-sm`) | LINE box btn 3/5/7 → Spot rounds warmer on purpose (Canva-lean); keep `--r-sm`. |
| Primary height | 44px desktop (`--control-h-lg`), **48px mobile** | LINE touch; Spot `index.html:1176`. |
| Primary fill | `--accent-grad` (`.hn-btn`) or solid `--accent`; text `--on-accent` | one indigo primary per screen. |
| Hover | grad-hover + `translateY(-1px)` + shadow; **70% opacity** rule for tonal/ghost | LINE hover = 70%. |
| Pressed | `translateY(0) scale(.98)`; **50% opacity** for ghost | LINE pressed = 50%. |
| Disabled | **label only** dims to `--faint`; shape/bg unchanged | LINE: disable label first. |
| Loading | inner `.spin` (18px) replaces label; button stays same width | LINE Box Button Loading state. |
| Pairing | horizontal → **primary right**; vertical → **primary top**; never 2 same-weight primaries | LINE Box Button. |
| Icon button | container **32px (S) / 40px (desktop `--target`) / 52px (L)**; hover bg `--hover` | LINE Icon Button S32/L52. |
| Capsule (scroll pill) | height **42px**, padding `~26/7/16`, radius `--r-full` | LINE Capsule Button. |
| FAB | **56px** dia (LINE 54pt), icon ~32px, `--accent-grad`+`--glow`, bottom-right **16px** | LINE FAB. |

### Cards

| Property | Value |
|---|---|
| Radius | `--r-lg` **20px**; `overflow:hidden` for full-bleed thumbs |
| Border / rest shadow | `1px --line` / `--shadow-1` |
| Hover | `translateY(-3px)`, `--shadow`, border `--line-strong` |
| Active | `translateY(-1px) scale(.99)` |
| Inner content margin | **16px** (LINE card content margin) |
| Thumb | full-bleed top; 4:3 / 16:9 / 1:1 / 9:16 supported (LINE Card + Image Grid) |
| Indicators | corners, **non-tappable**, glassy (`rgba(12,12,18,.72)`+blur); status dot, duration `00:15`, format |
| Primary action | **whole card**; supplemental (⋯) = separate icon btn, stops propagation |

### Option / choice cards (`.opt`) — the signature component

| Property | Rest | Selected |
|---|---|---|
| Min height | 96px desktop / 84px mobile | — |
| Padding / radius | 16px / `--r-md` (14px) | — |
| Background | `--surface` | `color-mix(--accent-soft 55%, --surface)` |
| Border | `1px --line` | `--accent-ink` |
| Icon chip | 40×40, `--r-sm`, `--surface-2`, glyph `--accent-ink` | solid `--accent`, glyph `--on-accent` |
| Tick (top-right) | 20px hollow, `1.5px --line-strong`, transparent | `--accent` fill, `--on-accent` ✓, snaps in `--ease-spring` |
| Hover | `translateY(-3px)`, `--shadow`, `--ease-spring` 200ms | — |
| Glow | — | faint `--glow` behind card |
| Selection logic | multi = ✓ each (Filter); single = auto-clear others (Choice) | show mark, not color alone |

### Bottom sheet (new, mobile)

| Property | Value |
|---|---|
| Top radius | **14px** fixed (LINE) |
| Width / margin | 100% / 0 |
| Surface / elevation | `--surface` / `--shadow-lift` |
| Handlebar | present (grab); header = **Close-only** default, title left |
| Dimmer | Modal (blocks, `--scrim`) for required choices; Interactive (no dimmer) rarely |
| Buttons | vertical, **single primary** ("決定"); 3 buttons discouraged |
| Image aspect (if used) | 375-wide: 16:9=210 / 4:3=281 / 1:1=375 / 3:4=500 |
| Motion | slide-up `--dur-slow --ease-emphasized`; dimmer fade `--dur` |

### Chips / badges / filters

| Item | Value |
|---|---|
| Chip radius | `--r-full` (pill), padding fixed, width = content |
| Chip roles | Action (do) / **Filter** (multi, ✓/＋, re-tap clears) / Choice (single, auto-clears prev) |
| Filter (`.filter`) | selected = fill + count; `aria-pressed` (already) |
| Badge Dot | 5 / 8 / 10 / 14 / 20px (S–XXL) |
| Badge Number height | 16 / 18 / 20 / 24 / 36px; overflow **99+** (LDSG) / 999+ (msgr) |
| Badge color | nav/GNB = `--crit` red; else `--accent` |

### Tabs / segmented (result format, view switches)

| Item | Value |
|---|---|
| Tab underline | **2px** (M) / 1px (S), `--accent-ink` |
| States | selected 100% + bold + underline; hover 70%; pressed 50% |
| Count | Fixed **2–4** equal-width; >4 → Flexible horizontal scroll |
| Segmented | height 32/36/44 (S/M/L); 2–4 items; place *below* tabs, not above |

### Empty states

| Item | Value |
|---|---|
| Composition | (pictogram, optional) + title + description + **1 button** (max 2), centered |
| Icon tile | 60×60, `--r-lg`, `--accent-soft`, glyph `--accent-ink` (`.empty .e-ic`) |
| Voice | calm, partner tone; **no urgency / no CTA-shout** (LINE) |
| Placement | Large = full-screen center; Small = module center |

### Avatars

Radius `50%`; diameter scale **24 / 32 / 42 / 50 / 60 / 72 / 118px** (XXS–XXL). Badge (dot/number) only from S+ ; hover 70% / pressed 50%. Standardize Spot's scattered avatar sizes (sidebar 32, menu-head 40→use 42, etc.).

### Progress / spinner / skeleton

| Item | Value |
|---|---|
| Circular progress | dia **20 / 26 / 40 / 52px**, stroke **2.5 / 3 / 3 / 5px**; track `--surface-2`, indicator `--accent` |
| Spinner (`.spin`) | 30×30, clockwise continuous; center of module/dialog |
| Skeleton (`.skel`) | shimmer top-left→bottom-right, base `--surface-2`; **never** with a spinner |
| Generation wait | Circular M(40) + `--glow` pulse + honest status line ("台本を書いています…") |

### Tooltip / coachmark (new — first-run)

| Item | Value |
|---|---|
| Max text | **3 lines**; Large = has button, Small = 1 line no button |
| Position | ≥8px from screen edge; **2–8px** from target |
| Padding / close | 12/11px; close 14px right / 13px top |
| Rule | **one per page**; avoid over a dimmed screen |
| Use | onboarding: point at FAB / hero / first option card |

### Page indicator (wizard)

Dot **5px inactive / 7px active**; active `--accent-ink`, inactive `--outline`; gap 8px; **16px** outer / 12px inner margin. Number style height 18/22px, bg `black 40%` — dots preferred for ≤5 steps.

### Toast / snackbar (feedback)

| Item | Toast | Snackbar |
|---|---|---|
| Actions | **none** | can have 1 action (`--accent-ink`) |
| Auto-dismiss | ~4s | ~3s (4–10 selectable) |
| Background | `black 80%` | `black 85%` |
| Bottom margin | 16px; width = screen − 32 | 16px |
| Count | **always 1** | 1 |

Spot's `window.toast(msg, ok, ms)` → default `ms` 3000–4000, enforce single instance.

---

## 4. Motion & micro-interaction spec

LINE's Feedback guideline: **≥1 feedback per user action**, via Component / Motion / Transition / Haptic — combined within reason, never disruptive. Spot's tokens already encode M3 easings; this is where to spend them.

### Easings & durations (from `tokens.css`, keep as-is)

| Token | Value | Use |
|---|---|---|
| `--ease-standard` | `cubic-bezier(.2,0,0,1)` | color/opacity, hovers, small moves |
| `--ease-emphasized` | `cubic-bezier(.05,.7,.1,1)` | **arrive**: content/step/view in, sheet up |
| `--ease-spring` | `cubic-bezier(.34,1.4,.64,1)` | **commit**: option select, tick snap, FAB |
| `--dur-fast` | 120ms | hover, tick, micro-fades |
| `--dur` | 200ms | most transitions, tab cross-fade |
| `--dur-slow` | 320ms | arrivals, step change, reveal, sheet |

### Where motion earns its place

| Moment | Motion | Tokens |
|---|---|---|
| View enter | fade + 8px lift up | `--dur-slow --ease-emphasized` (already `main`) |
| Wizard step change | out fade+lift 8px (`--dur-fast`); in question + **stagger cards** (+12ms each, y8→0) | `--dur-slow --ease-emphasized` |
| **Option select ("thunk")** | bg fill + border + icon fill; **tick scales 0→1 with overshoot**; card settles | `--ease-spring`, `--dur-fast`→`--dur` |
| Option hover | lift 3px + shadow, tiny springy overshoot | `--ease-spring` 200ms |
| Progress bar / dots | width/active-dot animate | `--dur-slow --ease-emphasized` |
| FAB idle → tap | subtle `--glow` breathe (opt-in); press scale .96 | `--ease-spring` |
| Bottom sheet | slide up from 100%; dimmer fade in | `--dur-slow --ease-emphasized` / `--dur` |
| Toast | slide up + fade in, auto-out after 3–4s | `--dur --ease-emphasized` |
| Skeleton → content | shimmer, then content cross-fades in (no spinner) | `--dur --ease-standard` |
| **Result reveal** | player 96%→100% + fade, `--glow` bloom once, one Toast | `--dur-slow --ease-emphasized` |
| Menus/popovers | scale from origin corner | already `menu-in` |

Rules: never animate more than the thing that changed; overshoot **only** on *commit* (select/FAB) so "springy" reads as "pickable"; all gated by `prefers-reduced-motion` (extend the existing `@media` block to cover `.opt` tick, sheet, stagger). Haptic: n/a on web — substitute a crisp visual "thunk" on select.

---

## 5. Prioritized build list (bold, non-breaking)

Ordered by impact. Effort: S ≤ half-day, M ≈ 1–2 days, L ≈ 3+ days. ★ = highest-leverage on the "選ぶだけ" feeling.

| # | What changes | Effort |
|---|---|---|
| 1 ★ | **Option-card "thunk"**: bigger `.opt` (96/84px), spring hover, select = indigo fill + solid icon + snapping ✓ tick + faint glow; single vs multi logic shows the mark | **M** |
| 2 ★ | **`--glow` primitive**: extract the hero aura into a token/util; apply behind hero, selected options, FAB, result reveal | S |
| 3 ★ | **One-question wizard**: promote active `.step-q` to `--t-display`, demote everything else; JP helper under it | S |
| 4 ★ | **Mobile FAB「新規CM」** (56px, bottom-right 16px, `--accent-grad`+glow, single action) | S |
| 5 | **Wizard progress**: dot Page Indicator (5/7px) under question + upgrade left `.step-nav` into a connected spine | M |
| 6 | **Step transition**: out-fade + staggered card arrival (`--ease-emphasized`) | S |
| 7 | **Footer nav decisive**: primary-right, 48px mobile, disabled-until-answered (label-only dim), final step = 「CMをつくる」 + `.spin` loading | S |
| 8 ★ | **Mobile bottom sheet** for many-option steps (14px top radius, handlebar, close-only header, single vertical primary, modal dimmer) | **L** |
| 9 | **Home result cards → LINE Card**: full-bleed thumb, non-tappable status/duration/format indicators, whole-card tap, ⋯ supplemental separate | M |
| 10 | **Empty state as first-run hero**: pictogram tile + calm partner-voice copy + single button; wire 1–2 coachmark Tooltips | M |
| 11 | **Result "premiere" reveal**: player scale-up + glow bloom + single Toast; format tabs 2px underline; gradient scrim on any on-video text | M |
| 12 | **Feedback/motion pass**: single-instance Toast (3–4s, black 80%), skeleton-not-spinner everywhere, extend reduced-motion coverage | S |
| 13 | **Tooltip/coachmark component** (3-line max, ≥8px edge, one per page) for onboarding | M |
| 14 | **Avatar + circular-progress scales** standardized to LINE numbers; generation-wait uses Circular M(40) + glow + honest status text | S |

**Sequence:** ship 1–4 first (they carry 80% of the "choosing feels great" payoff for ~2 days work), then 5–7 (wizard clarity), then 8–11 (mobile + surfaces), then 12–14 (polish/onboarding). Every item is additive on existing classes/tokens — no rename, no breaking change.
