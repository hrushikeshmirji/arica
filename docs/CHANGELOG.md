# Changelog

All notable changes to the ArecaVision AI project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - Phase 2 Landing Page Visual Recreation Matching Reference Mockup (2026-10-12)

### Added
- **Design System Specification:**
  - `docs/DESIGN.md`: Single source of truth design system specification establishing botanical emerald palette (`#047857` / `#10b981`), restrained neutral scales, 5-step clinical severity tokens (`healthy`, `mild`, `moderate`, `severe`, `critical`), trilingual typographic hierarchy, and WCAG 2.1 AA accessibility standards.
- **Botanical Imagery Assets (`FRONTEND/public/`):**
  - `hero_palm.jpg`: Photorealistic high-resolution photograph of an arecanut palm tree with ripe orange betel nuts in a sunny tropical plantation.
  - `hero_leaf_frond.png`: Transparent foreground arecanut palm leaf frond for layered depth.
  - `samples/sample_healthy_leaf.jpg`: Lush healthy arecanut palm leaf frond thumbnail for the specimen gallery.

### Changed
- **Visual Recreation of Landing Page (`FRONTEND/src/pages/Landing.tsx`):**
  - Recreated visual layout, composition, typography, and section hierarchy matching the user's reference mockup.
  - **Navigation Bar:** Clean surface navbar with brand logo, subtitle, in-page navigation anchors (`Home`, `How It Works`, `Examples`, `Features`, `About`), language dropdown (`en`, `kn`, `hi`), theme toggle, and green `Launch AI Detection Studio` primary button. Responsive navbar breakpoints (`hidden lg:flex` for text links) prevent horizontal overflow on tablet and desktop viewports.
  - **Asymmetric Hero:** Two-line bold editorial headline ("SEE THE SIGNS." in dark slate, "SAVE THE HARVEST." in deep botanical emerald green), supporting copy, dual CTAs (`Launch AI Detection Studio` and `Explore Specimen Examples`), and 4 proof benefit indicators (`Easy to Use`, `Mobile Friendly`, `AI-Powered`, `Actionable Guidance`).
  - **Hero Botanical Composition:** Right column featuring `hero_palm.jpg`, circular green backdrop glow, floating diagnostic-preview panel with simulated YOLO bounding boxes on `sample_leaf_spot.jpg` (`Detected Disease Regions`), clinical analysis result panel with `Moderate` severity badge, and layered foreground leaf frond (`hero_leaf_frond.png`). Mobile container height (`min-h-[470px]`) frames the diagnostic card cleanly, and the decorative frond is hidden on small screens (`hidden sm:block`) to prevent obstructing diagnostic copy.
  - **Common Arecanut Disease Cases Gallery:** Horizontal gallery of 5 real supported specimens (`Healthy Leaf`, `Leaf Spot`, `Koleroga`, `Stem Bleeding`, `Yellow Leaf`) with interactive card selection, scroll controls, and detailed agronomic treatment drawer displaying symptoms, ICAR chemical spray dosages, and organic bio-control protocols.
  - **3-Stage AI Pipeline:** 3 connected sequential stage cards (Stage 1 Gatekeeper with EfficientNet-B0 dual thresholds, Stage 2 Disease Detection with YOLOv8 spatial localization, Stage 3 Disease Classification with ViT-B/16 multi-scale transformer) alongside botanical canopy photography and clear explanatory copy.
  - **Pathology Catalog & Bottom CTA:** 8-disease grid with direct links to the Detection Studio and Disease Library, zero-hardware CTA banner, and clean botanical footer.
  - **Diagnostic Preview Safety Clarification:** Explicitly labeled the hero diagnostic preview as illustrative demo data (`DEMO DATA` viewport tag, `Leaf Spot 92.4% (Simulated)` bounding box label, and trilingual `ILLUSTRATIVE PREVIEW` badge on the analysis result header) to ensure zero false implication of live inference while strictly preserving visual composition and leaving all real Detection Studio workflows untouched.
  - **Trilingual & Accessibility:** Complete English, Kannada (`kn`), and Hindi (`hi`) translation dictionaries with `leading-relaxed` line-height headroom to prevent Indic script clipping; WCAG 2.1 AA focus rings, semantic HTML, and `prefers-reduced-motion` compliance.
  - **Diagnostic Pipeline Fixes & Resilience:**
    - Fixed specimen extraction in `FRONTEND/src/services/detectionService.ts` where JavaScript `split(":", 1)` sliced the array length and sent `specimenId: undefined`.
    - Enhanced `FRONTEND/src/services/apiClient.ts` to surface actionable connectivity diagnostics when the FastAPI backend on port 8000 is offline instead of generic browser `Failed to fetch`.
    - Hardened `FRONTEND/src/components/XaiSplitViewer.tsx` to initialize and synchronize mode dynamically (`split` only when attention map is present; `original` otherwise) and accurately label un-localized detections.
    - Added `"backend"` runner script to root `package.json` (`npm run backend`) to simplify starting the FastAPI neural engine.
- **Styling Architecture (`FRONTEND/src/index.css`):**
  - Added `@custom-variant dark (&:where(.dark, .dark *));` to ensure class-based dark mode toggling works seamlessly in Tailwind CSS v4.
  - Added `@media (prefers-reduced-motion: reduce)` block to instantly suppress animations and transitions for users with vestibular sensitivities or OS motion reduction preferences.
- **Verification:**
  - 100% production build pass (`npm run build` in 875ms).
  - 19/19 Vitest unit tests passing (`npm test`).
  - Verified zero horizontal overflow across 1440px (desktop), 1024px (small laptop), 768px (tablet), and 375px (mobile) viewports via Playwright DOM evaluation (`scrollWidth === clientWidth`).

---

## [2.1.0] - Phase 1 Baseline Hardening (2026-10-12) — Commit: `66509a5`

### Changed
- **Version Control & Repository Hygiene:**
  - Untracked `backend/arecavision.db` from Git index (`git rm --cached`) to prevent local runtime databases from being committed.
  - Untracked `backend/tests/results/auth_check.json` to prevent serialized JWT tokens from leaking into commits.
  - Hardened `.gitignore` to comprehensively exclude local database patterns (`*.db`, `*.db-wal`, `*.db-shm`, `*.sqlite`, `*.sqlite3`), backup copies (`*.bak`, `*.backup`, `.backup/`), and sensitive test outputs.
  - Preserved local copies of runtime databases and test logs on disk and in local backups before untracking.

### Added
- **Project Documentation (`docs/`):**
  - `docs/CHANGELOG.md`: Verified historical baseline and release tracking.
  - `docs/FEATURES.md`: Comprehensive breakdown of verified operational capabilities versus unverified/mock-backed features.
  - `docs/ARCHITECTURE.md`: Technical documentation of the React 19 frontend, FastAPI microservice, SQLite storage, and 3-stage ML pipeline.
  - `docs/ROLLBACK_GUIDE.md`: Safe Git checkpoints, feature-specific rollback steps, and recovery precautions.

---

## [2.0.0] - Verified Baseline Commit: `35b3b90` (2026-10-12)

### Added
- **Clean Dataset Generation:**
  - Added `backend/build_clean_dataset.py` creating `backend/data/clean_dataset_manifest.json` and `backend/data/clean_dataset_summary.json`.
  - Filtered 130 cross-class image conflicts and quarantined synthetic seed images to train-only to eliminate validation data leakage.
  - Added end-to-end dataset verification test suite.

---

## [1.9.0] - Commit: `b65bc88` (2026-10-12)

### Fixed
- **Inference Pipeline & UI Localization:**
  - Implemented unclamped gate scoring in Stage-1 Gatekeeper inference.
  - Implemented experimental vs. validated class routing in Stage-3 ViT output.
  - Synchronized Kannada (`kn`) and Hindi (`hi`) agronomic localization in UI components.

---

## [1.8.0] - Commit: `932874e` (2026-10-12)

### Security & Hardening
- Hardened Stage-1 Gatekeeper and ViT inference thresholds.
- Removed synthetic bounding box generation from YOLO inference fallbacks.
- Corrected marketing and performance claims across frontend services.

---

## [1.5.0] - Commit: `0ec7562` (2026-10-09)

### Changed
- Permitted unauthenticated guest access to public clinical routes (`/detection` and `/diseases`).
- Added simplified landing page walkthrough for first-time farmers and agronomists.
