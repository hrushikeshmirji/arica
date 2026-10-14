# ArecaVision AI 2.0 — Design System Specification

## 1. Executive Summary & Design Philosophy

ArecaVision AI is an enterprise-grade precision agricultural diagnostic platform designed for arecanut (*Areca catechu*) crop health, pathology detection, and plantation management. The design system bridges field utility for growers in South India with clinical rigor for research agronomists.

### Core Design Principles
1. **Dignified Botanical Editorial**: A clean, scientific visual language grounded in botanical emerald green (`#047857`) and balanced neutrals (slate/zinc). The interface feels like an authoritative phytosanitary workbench rather than a generic SaaS dashboard.
2. **Restraint Over Spectacle**: No gratuitous neon gradients, overdone glassmorphism, decorative blur cards, or distracting idle animations. Every visual element has a functional diagnostic purpose.
3. **Strict Accessibility & Contrast**: All typography meets WCAG 2.1 AA contrast requirements (minimum 4.5:1 for body text, 3:1 for large text). Severity colors are distinct and paired with text labels and iconography for color-blind accessibility.
4. **Trilingual Typographic Integrity**: Full typographic dignity for Kannada (`kn`), Hindi (`hi`), and English (`en`), providing adequate vertical leading to prevent clipping of Indic vowel diacritics and conjuncts (*ottakshara* / *matras*).
5. **Deterministic Iconography**: Consistent Lucide SVG icons (`lucide-react`) used exclusively; no informal emoji icons in headers, buttons, or status pills.

---

## 2. Color System & Semantic Tokens

### 2.1 Primary & Neutral Palette (Light vs. Dark)

Mapped to Tailwind CSS v4 `@theme inline` variables defined in `FRONTEND/src/index.css` and `FRONTEND/src/theme/tokens.ts`:

| Token | Light Theme Value | Dark Theme Value | Semantic Role |
|---|---|---|---|
| `--color-primary` | `#047857` (Emerald 700) | `#10b981` (Emerald 500) | Primary brand accent, primary CTA buttons, active indicators |
| `--color-primary-hover` | `#065f46` (Emerald 800) | `#059669` (Emerald 600) | Interactive hover state for primary elements |
| `--color-primary-foreground` | `#ffffff` | `#042f2e` (Emerald 950) | High-contrast text on primary background |
| `--color-background` | `#f8fafc` (Slate 50) | `#09090b` (Zinc 950) | Main application background canvas |
| `--color-surface` | `#ffffff` | `#18181b` (Zinc 900) | Secondary surface / elevated panel background |
| `--color-card` | `#ffffff` | `#121215` (Zinc 925) | Base card, container, and dialog background |
| `--color-card-hover` | `#f1f5f9` (Slate 100) | `#27272a` (Zinc 800) | Card hover interaction state |
| `--color-secondary` | `#f1f5f9` (Slate 100) | `#27272a` (Zinc 800) | Secondary button and inactive badge background |
| `--color-muted` | `#e2e8f0` (Slate 200) | `#27272a` (Zinc 800) | Subdued backgrounds, horizontal rules, table dividers |
| `--color-muted-foreground` | `#64748b` (Slate 500) | `#94a3b8` (Slate 400) | Secondary labels, captions, helper text, timestamps |
| `--color-border` | `#e2e8f0` (Slate 200) | `#27272a` (Zinc 800) | Restrained hairline component borders |
| `--color-input` | `#e2e8f0` (Slate 200) | `#27272a` (Zinc 800) | Form input border |
| `--color-ring` | `#047857` (Emerald 700) | `#10b981` (Emerald 500) | Keyboard focus ring |

### 2.2 Semantic State Tokens

| Semantic Role | Token | Light Value | Dark Value | Text on Light | Text on Dark |
|---|---|---|---|---|---|
| **Success** | `--color-success` | `#047857` | `#10b981` | `#065f46` | `#34d399` |
| **Warning** | `--color-warning` | `#b45309` | `#fbbf24` | `#92400e` | `#fde68a` |
| **Danger / Error** | `--color-danger` | `#dc2626` | `#f87171` | `#991b1b` | `#fca5a5` |
| **Info / Accent** | `--color-accent` | `#0ea5e9` | `#38bdf8` | `#0369a1` | `#7dd3fc` |

### 2.3 5-Step Clinical Severity Scale Tokens

Standardized across diagnostic badges, GIS block maps, scan history, and Recharts graphs:

| Severity Level | CSS Variable / Token | Hex Value (Light) | Hex Value (Dark) | Badge Background (Light/Dark) | Clinical Definition |
|---|---|---|---|---|---|
| **Healthy** | `--severity-healthy` | `#047857` | `#10b981` | `#ecfdf5` / `rgba(16, 185, 129, 0.15)` | No pathology detected; optimal vigor |
| **Mild** | `--severity-mild` | `#3b82f6` | `#60a5fa` | `#eff6ff` / `rgba(59, 130, 246, 0.15)` | Early chlorosis or minor leaf spotting |
| **Moderate** | `--severity-moderate` | `#b45309` | `#fbbf24` | `#fffbeb` / `rgba(245, 158, 11, 0.15)` | Localized nut splitting or sap lesion |
| **Severe** | `--severity-severe` | `#f97316` | `#fb923c` | `#fff7ed` / `rgba(249, 115, 22, 0.15)` | Active anthracnose dieback or crown rot |
| **Critical** | `--severity-critical` | `#dc2626` | `#f87171` | `#fef2f2` / `rgba(220, 38, 38, 0.15)` | Koleroga (Fruit Rot) epidemic; emergency spray |

---

## 3. Typography & Trilingual Guidance

### 3.1 Font Families & Fallbacks
```css
/* Primary UI Font Stack (Latin / English) */
font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;

/* Kannada Fallback Stack */
font-family: "Inter", "Noto Sans Kannada", "Tunga", "Kedage", sans-serif;

/* Hindi (Devanagari) Fallback Stack */
font-family: "Inter", "Noto Sans Devanagari", "Mangal", "Aparajita", sans-serif;

/* Monospace Stack (Timings, Job IDs, Coordinates) */
font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
```

### 3.2 Type Scale & Hierarchy

| Role | Class | Desktop Size / Leading | Mobile Size / Leading | Weight | Tracking |
|---|---|---|---|---|---|
| **Display / Hero** | `text-4xl` to `text-5xl` | 44px–48px / 1.15 | 32px–36px / 1.20 | 800 (Extrabold) | `-0.025em` |
| **Page Title (H1)** | `text-2xl` to `text-3xl` | 28px–30px / 1.25 | 24px / 1.30 | 700 (Bold) | `-0.02em` |
| **Section Header (H2)**| `text-xl` to `text-2xl` | 22px–24px / 1.30 | 20px / 1.35 | 700 (Bold) | `-0.015em` |
| **Card Title (H3)** | `text-base` to `text-lg` | 17px–18px / 1.35 | 16px / 1.40 | 600 (Semibold) | `-0.01em` |
| **Body (Regular)** | `text-sm` | 14px / 1.50 | 14px / 1.50 | 400 (Regular) | `normal` |
| **Body (Dense/UI)** | `text-xs` | 12px / 1.45 | 12px / 1.45 | 500 (Medium) | `normal` |
| **Caption / Meta** | `text-[11px]` | 11px / 1.40 | 11px / 1.40 | 500 (Medium) | `+0.01em` |
| **Overline / Badge** | `text-[10px]` uppercase | 10px / 1.20 | 10px / 1.20 | 700 (Bold) | `+0.08em` |

### 3.3 Trilingual Line-Height & Layout Rules
- **Indic Script Clearance**: Kannada and Devanagari feature vertical vowel matras, superscript signs, and subscript conjuncts (*ottakshara*). When rendering `language === "kn"` or `language === "hi"`, enforce `leading-relaxed` (`line-height: 1.625`) to prevent vertical glyph clipping.
- **Badge & Button Containers**: Do not apply fixed height (`h-6`, `h-8`) to text containers with multilingual translations. Use flexbox with vertical padding (`py-1`, `py-1.5`) and min-height (`min-h-[28px]`, `min-h-[36px]`).
- **Font-Weight Restraint in Kannada**: Avoid ultra-bold weights (`font-black` or `font-extrabold`) on complex Indic glyphs as dense letterforms fill in counters. Cap Kannada display weights at `font-bold` (700).

---

## 4. Spacing, Layout & Responsive Grid

### 4.1 Breakpoints & Container Constraints
Standardized on Tailwind CSS defaults:
- **Mobile (`sm`)**: `640px`
- **Tablet (`md`)**: `768px`
- **Desktop (`lg`)**: `1024px`
- **Workstation (`xl`)**: `1280px`
- **Max Width**:
  - Landing Page Hero: `max-w-4xl` (896px) for focused reading.
  - Landing Content Sections: `max-w-5xl` (1024px) or `max-w-6xl` (1152px).
  - Diagnostic & Dashboard Studio: `max-w-7xl` (1280px).

### 4.2 Spacing Scale
- Component Padding: `p-4` (16px) on mobile $\to$ `p-6` (24px) on tablet/desktop.
- Section Vertical Rhythm: `py-12` (48px) to `py-16` (64px) for landing sections.
- Grid Gaps: `gap-3.5` (14px) for compact cards $\to$ `gap-6` (24px) for major column splits.

### 4.3 Borders, Radii & Shadows
- **Hairline Borders**: `1px solid var(--color-border)` throughout. Clean separation without heavy drop-shadows.
- **Corner Radii Hierarchy**:
  - Small elements (badges, pills, inputs, buttons): `rounded-md` (6px) or `rounded-lg` (8px).
  - Cards, panels, modals: `rounded-xl` (12px).
  - Outer dialogs, full preview wrappers: `rounded-2xl` (16px).
- **Subtle Elevation**:
  - Default: `shadow-xs` (`0 1px 2px rgba(0,0,0,0.05)`)
  - Elevated Popovers/Modals: `shadow-md` (`0 4px 6px -1px rgba(0,0,0,0.1)`)
  - Avoid heavy, colored blur shadows (`shadow-[0_0_50px_rgba(...)]`).

---

## 5. Component Patterns & Conventions

### 5.1 Buttons
- **Primary Action** (`.btn-primary`):
  - Background: `var(--color-primary)` (Emerald 700 / 500)
  - Text: High contrast white (Light) or deep emerald 950 (Dark)
  - Hover: `hover:bg-primaryHover` with subtle transition (`transition-colors duration-150`).
  - No hover jump / transform bounce (`transform: translateY(-1px)` removed to prevent jitter).
- **Secondary Action** (`.btn-secondary`):
  - Background: `var(--color-card)`, Border: `1px solid var(--color-border)`
  - Text: `var(--color-foreground)`
  - Hover: `hover:bg-card-hover hover:border-neutral-300 dark:hover:border-neutral-700`
- **Ghost / Tertiary**:
  - Background: transparent, Text: `var(--color-muted-foreground)`
  - Hover: `hover:text-foreground hover:bg-muted/50`

### 5.2 Form Inputs & Controls
- **Text Inputs & Selects**:
  - Background: `var(--color-card)`, Border: `1px solid var(--color-border)`
  - Text: `var(--color-foreground)`, Placeholder: `var(--color-muted-foreground)`
  - Height: `h-10` (40px) or `h-11` (44px for touch targets)
  - Focus Ring: `focus-visible:outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20`
- **File Upload / Dropzone**:
  - Border: `2px dashed var(--color-border)`, Hover: `border-primary bg-primary/5`
  - Clear drag-and-drop affordance with supported file formats list (`JPEG, PNG, WEBP, BMP up to 10 MB`).

### 5.3 Diagnostic Result & Severity Badges
- **Structure**: High-contrast pill featuring SVG icon, uppercase severity text, and clear percentage.
- **Format**:
  ```tsx
  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold uppercase tracking-wider bg-red-50 text-red-700 border border-red-200 dark:bg-red-950/40 dark:text-red-400 dark:border-red-900/50">
    <AlertTriangle size={13} aria-hidden="true" />
    Critical Severity
  </span>
  ```

### 5.4 Navigation Shell (`FRONTEND/src/components/Layout.tsx`)
- Sidebar layout on desktop (`w-64`), collapsible overlay on mobile.
- Active items use `.nav-item-active` with solid left indicator pill (`w-1 rounded-full bg-primary`).
- Direct keyboard shortcuts mapped via global `CommandPalette` (`Ctrl+K` / `Cmd+K`).

---

## 6. Accessibility, Navigation & Motion (WCAG 2.1 AA)

### 6.1 Contrast Verification
- All text on background surfaces guarantees a contrast ratio $\ge 4.5:1$.
- UI borders and graphical control indicators maintain $\ge 3:1$ contrast against adjacent canvas.
- No information is conveyed by color alone: all status indicators (Healthy, Warning, Critical) must pair color with textual naming and distinctive iconography.

### 6.2 Visible Keyboard Focus
- Global outline suppression (`outline-none`) must **always** be accompanied by `focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2`.
- Modal dialogs must trap focus (`useFocusTrap.ts`) and return focus to the trigger on close.

### 6.3 Reduced Motion (`prefers-reduced-motion`)
- Respect system accessibility preferences:
  ```css
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
  }
  ```

---

## 7. Landing Page Design Architecture (`/`)

### 7.1 Section Flow & Information Hierarchy
1. **Header / Navbar**:
   - Clean logo with leaf mark, app title, trilingual selector (`EN / KN / HI`), theme toggle, and direct "Scan Photo" CTA button.
2. **Hero Section (Conversion-Focused)**:
   - Clear value proposition: *"Lab-grade Arecanut disease diagnosis from a phone photo in seconds."*
   - Direct, actionable dual CTA:
     - Primary: `[Camera icon] Scan a Photo Now` (`/detection`)
     - Secondary: `See Sample Diagnosis Below ↓` (scroll anchor `#see-example`)
   - Proof points badge: 100% Free • Smartphone Ready • ICAR Spray Dosages • Field Validated.
3. **How It Works (3 Steps)**:
   - Step 1: Take Photo (Clear natural light palm image)
   - Step 2: Upload Here (Automatic Gatekeeper defense check)
   - Step 3: Get Exact Medicine (ICAR spray dosage + organic alternatives)
4. **Interactive Clinical Specimen Workbench**:
   - Tab switcher for verified field conditions: Fruit Rot (Koleroga), Leaf Blight (Anthracnose), Nut Splitting, and Healthy Palm.
   - High-contrast card showing sample photo alongside diagnosis: disease name, confidence match, symptoms, chemical spray dosage, and organic controls.
5. **3-Stage Defense Explanation (Trust & Science)**:
   - Explains Stage 1 Gatekeeper (rejects non-arecanut foliage, weeds, background), Stage 2 YOLOv8 (pinpoints lesions), Stage 3 ViT (diagnoses pathology). Builds grower trust that non-arecanut crops will not trigger false alarms.
6. **Diseases Covered Grid**:
   - Clean 5-card grid summarizing primary pathologies with Kannada transliterations.
7. **Final Action Banner & Footer**:
   - Uncluttered prompt to scan, accompanied by legal, clinical disclaimer, and navigation links.

### 7.2 Non-Exaggeration Policy
- **Factual Claims Only**: Never claim partnerships, government certifications, or field trials that are not empirically verified.
- **Clear Disclaimers**: Clarify that recommendations follow standard ICAR/agricultural university agronomic guidelines, but growers should consult local Krishi Vigyan Kendras (KVK) for systemic plantation outbreaks.

---

## 8. Dashboard, Detection Studio & State Management

### 8.1 State Handling Rules

Every UI container that fetches or processes asynchronous data must implement 4 explicit visual states:

```
┌────────────────────────────────────────────────────────┐
│  1. LOADING STATE                                      │
│     Subtle skeleton placeholder with shimmer (no spin) │
├────────────────────────────────────────────────────────┤
│  2. EMPTY STATE                                        │
│     Specific Lucide icon, explanatory copy, and CTA    │
├────────────────────────────────────────────────────────┤
│  3. ERROR STATE                                        │
│     Amber/Red alert banner, failure reason, and Retry  │
├────────────────────────────────────────────────────────┤
│  4. SUCCESS / DATA STATE                               │
│     High-density cards, true data metrics, no mocks    │
└────────────────────────────────────────────────────────┘
```

1. **Loading State**:
   - Use skeleton blocks with subtle pulse (`bg-muted/40 animate-pulse rounded-md`) reflecting the exact card geometry.
   - For diagnostic inference, display progressive step milestones:
     - `1/3 Gatekeeper Defense Check...`
     - `2/3 YOLO Lesion Localization...`
     - `3/3 ViT Multi-Scale TTA Classification...`
2. **Empty State**:
   - When no scans exist in `backend/data/arecavision.db`, show an illustration/icon (`Inbox` or `Camera`), friendly heading ("No scans recorded yet"), and an immediate action button ("Upload First Palm Photo").
3. **Error State**:
   - Display actionable error feedback: distinguish network offline failures, invalid file formats (e.g. non-image upload), and model rejection errors.
   - For Gatekeeper Rejection, provide clear multilingual guidance: *"Photo rejected: Gatekeeper could not verify arecanut palm tissue. Please retake photo."*
4. **Success State**:
   - Render real clinical telemetry: true YOLO bounding boxes with model confidence $\ge 0.25$, attention rollout heatmap, and differential diagnosis candidate table.

---

## 9. Alignment Audit: Existing Code vs. Design System

| Dimension | Current Implementation in Code | Design System Specification | Action / Migration Path |
|---|---|---|---|
| **Icons** | Emojis used in language selector (`🌐`), footer (`🌿`), and specimen cards | Strictly use Lucide SVG icons (`Globe`, `Leaf`, `CheckCircle2`) | Replace emojis with Lucide components during page polish |
| **Hover Transforms**| `transform: translateY(-1px)` in `.btn-primary` and `.card-hover` | Removed translateY to prevent micro-jitter and layout reflow | Migrate to subtle border/background transitions |
| **Kannada Line-Height**| Default Latin line heights causing tight Indic glyph rendering | Enforce `leading-relaxed` on Indic locale strings | Apply dynamic leading class when `language === "kn"` or `"hi"` |
| **Color Tokens** | Defined across `tokens.ts` and `index.css` | Reused exactly; consolidated into unified documentation | Full parity confirmed; no token changes required |
| **Tailwind Engine** | Native Tailwind CSS v4 (`@theme inline`) | Pure Tailwind v4 CSS variable mapping | Full parity confirmed |
