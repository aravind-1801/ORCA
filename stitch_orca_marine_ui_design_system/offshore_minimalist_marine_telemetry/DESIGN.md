---
name: Offshore Minimalist Marine Telemetry
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#43474b'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#73787c'
  outline-variant: '#c3c7cb'
  surface-tint: '#4e616e'
  primary: '#000306'
  on-primary: '#ffffff'
  primary-container: '#0b1f2a'
  on-primary-container: '#748895'
  inverse-primary: '#b5c9d8'
  secondary: '#006492'
  on-secondary: '#ffffff'
  secondary-container: '#7dc9ff'
  on-secondary-container: '#00547b'
  tertiary: '#000401'
  on-tertiary: '#ffffff'
  tertiary-container: '#00230a'
  on-tertiary-container: '#009a43'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d1e5f5'
  primary-fixed-dim: '#b5c9d8'
  on-primary-fixed: '#091e29'
  on-primary-fixed-variant: '#364955'
  secondary-fixed: '#cae6ff'
  secondary-fixed-dim: '#8bceff'
  on-secondary-fixed: '#001e2f'
  on-secondary-fixed-variant: '#004b6f'
  tertiary-fixed: '#7ffc97'
  tertiary-fixed-dim: '#62df7d'
  on-tertiary-fixed: '#002109'
  on-tertiary-fixed-variant: '#005320'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display-marine:
    fontFamily: Space Grotesk
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  display-marine-mobile:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 34px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: 0em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 26px
  headline-sm:
    fontFamily: Space Grotesk
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 22px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 26px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-numeric:
    fontFamily: Space Grotesk
    fontSize: 16px
    fontWeight: '700'
    lineHeight: 20px
    letterSpacing: 0.02em
  label-caps:
    fontFamily: Space Grotesk
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.06em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  page-margin-x: 16px
  touch-target-min: 48px
  gutter-sm: 8px
  gutter-md: 16px
  gutter-lg: 24px
  panel-pad-compact: 12px
  panel-pad-default: 16px
  panel-pad-spacious: 24px
---

## Brand & Style

This design system is engineered specifically for coastal fishermen operating under high-glare direct sunlight, salt spray, and turbulent physical conditions. It adopts a disciplined **Digital Minimalism and Flat Design 2.0** ethos: absolute clarity, purposeful utility, and instantaneous glanceability. Decorative chrome, non-functional ornamentation, simulated materials, glassmorphism, and neumorphism are strictly forbidden. 

The emotional tone is calm, authoritative, robust, and utilitarian. The user interface must feel like a precision nautical instrument—comparable to modern marine multi-function displays (MFDs) and bridge gauges—prioritizing immediate cognitive comprehension over decorative visual trends.

Visual hierarchy relies exclusively on high-contrast tone, calibrated typography weights, unambiguous status tokens, and architectural space.

## Colors

The palette is tuned to maintain legibility against polarized eyewear and midday coastal glare while minimizing eye fatigue during long watch shifts.

### Core Swatches
- **Primary (`#0B1F2A` — Deep Ocean Navy):** Grounding color for structural framing, core navigational chrome, high-priority readouts, and primary active states.
- **Secondary (`#1976A8` — Ocean Blue):** Interactive triggers, standard telemetry plots, informative indicators, and focus outlines.
- **Background (`#F7FAFC` — Pure Salt Surface):** Glare-controlled, ultra-clean neutral field that reduces retinal burn compared to pure `#FFFFFF`.
- **Card / Surface (`#FFFFFF` — Crisp Deck):** Elevated foreground panels providing sharp distinction against `#F7FAFC`.

### Marine Condition Tokens
Functional status indicators must never rely on color alone; each status color is paired with a distinct shape or text token:
- **Safe / Optimal (`#16A34A`):** Fair seas, clear navigational hazards, legal zone compliance, secure engine parameters.
- **Caution / Advisory (`#F59E0B`):** Squall watch, shoaling depth, approaching tide shift, cautionary engine RPMs.
- **Danger / Alert (`#DC2626`):** Collision warning, prohibited waters, severe storm front, engine failure, man-overboard alerts.

### Supporting Neutrals & Borders
- **Text Primary:** `#0B1F2A` (16.2:1 contrast ratio against `#FFFFFF`).
- **Text Secondary / Muted:** `#475569`.
- **Border / Divider:** `#E2E8F0` (clean, low-noise boundary for structural panels).

## Typography

The type system blends the geometric precision and high-aperture forms of **Space Grotesk** for numerical instrumentation and critical titles with the neutral, hyper-legible shapes of **Inter** for descriptions and logs.

### Numerical Readouts & Status Data
All critical metrics (knots, depth fathoms, wind speeds, heading bearings) utilize `Space Grotesk` with tabular figures enabled (`font-variant-numeric: tabular-nums`). This prevents jitter during continuous data streams.

### Glanceability Rule
Primary status badges and telemetry anchors deploy the `display-marine` or `display-marine-mobile` token. At 32–36px with bold weight, these values can be reliably interpreted at arm's length (30–36 inches) on a wheelhouse dashboard mount.

## Layout & Spacing

This design system uses a strict **8pt base grid** paired with a fluid column framework.

### Viewport Adaptation & Margins
- **Mobile Handheld (360px – 767px):** Single or dual-column stacked layout. Page margins are fixed at `16px` to conserve visual real estate while preserving safe thumb clearance.
- **Tablet Wheelhouse Display (768px – 1024px):** 6-column grid with `16px` gutters and `24px` margins. Readouts and navigation controls are anchored to the lower half or right edge for single-handed wet-weather operation.
- **Bridge Monitor / Desktop (1025px+):** 12-column layout with `24px` gutters and `32px` margins. Max container bounds locked at `1440px` to prevent excessive eye scanning across vast screen spans.

### Touch Target Mandate
All buttons, segment toggles, and tap zones must satisfy a minimum boundary of **48px × 48px** (exceeding standard 44px baselines) to accommodate thick commercial fishing gloves, water-droplet screen interference, and deck vibration.

## Elevation & Depth

In line with Flat Design 2.0 principles, this design system completely eliminates heavy drop shadows, blurred ambient lighting, and fake 3D extrusion. Direct sunlight washes out subtle shadows; physical deck shock makes delicate depth cues imperceptible.

### Depth Mechanisms
1. **Low-Contrast Structural Borders:** Surface containment relies on a crisp `1px solid #E2E8F0` border surrounding pure `#FFFFFF` panels on top of the `#F7FAFC` foundation.
2. **Tonal Tiering:** 
   - Level 0 (Base Canvas): `#F7FAFC`
   - Level 1 (Card / Gauge Container): `#FFFFFF` with `1px solid #E2E8F0`
   - Level 2 (Selected / Interacted Card): `#FFFFFF` with `2px solid #1976A8`
   - Level 3 (Critical Alert Modals): `#FFFFFF` with `2px solid #DC2626` and a crisp, unblurred 2px offset keyline (`0 2px 0 0 #0B1F2A1A`).

## Shapes

The design uses a restrained, functional corner rounding model (`level 1`). 

- Standard components (buttons, input fields, badges, telemetry cells) have `4px` (`0.25rem`) border radii.
- Surface cards and full-screen telemetry modules use `8px` (`0.5rem`).
- Strict rectangularity conveys industrial durability and maximizes active pixel area for data. Pill-shaped components are restricted exclusively to small status badges (`2px` radius) where capsule geometries differentiate badges from actionable buttons.

## Components

### Buttons
- **Primary:** Background `#0B1F2A`, text `#FFFFFF`, border none. Minimum height `48px`. Hover: `#1976A8`. Active/Pressed: `#061219`. Focus: `2px solid #1976A8` with 2px offset.
- **Secondary:** Background `#FFFFFF`, text `#0B1F2A`, border `1.5px solid #0B1F2A`.
- **Tertiary / Destructive Action:** Background `#DC2626`, text `#FFFFFF`, border none.
- **Padding:** `12px 20px`. Typography: `Space Grotesk`, `16px`, weight `700`.

### Status Badges & Glanceable Indicators
- Height: `32px` to `36px`.
- Layout: Inline horizontal flex with a `10px` solid status circle or icon followed by uppercase label text (`label-caps`).
- **Safe:** `#16A34A` text and accent indicator over `#F0FDF4` background with `1px solid #BBF7D0`.
- **Caution:** `#B45309` text over `#FFFBEB` background with `1px solid #FDE68A`.
- **Danger:** `#DC2626` text over `#FEF2F2` background with `1px solid #FECACA`.

### Telemetry Cards
- Surface: `#FFFFFF`.
- Border: `1px solid #E2E8F0`.
- Padding: `16px`.
- Structure: Header row contains metric label (`label-caps` in `#475569`) with unit of measure. Body shows prominent numerical metric in `display-marine` (`Space Grotesk`, 36px/32px, bold, tabular numbers). Footer contains micro-trend indicators or safe-range delta.

### Lists & Vessel Logs
- Table and list items feature alternating or clear row separators (`1px solid #F1F5F9`).
- Minimum row height: `56px` to ensure effortless gloved-thumb selection.
- Active item indicator: `4px` solid `#1976A8` left-border stripe.

### Inputs & Toggles
- **Form Controls:** Minimum height `48px`, background `#FFFFFF`, border `1.5px solid #CBD5E1`.
- **Radio Buttons & Checkboxes:** Base size `24px × 24px` with a `2px` border to ensure visibility on rolling decks.
- **Marine Toggle Switches:** High-contrast track (`#CBD5E1` inactive, `#1976A8` active) with `28px` high-visibility tactile thumb indicator.