# Design System Document

## 1. Overview & Creative North Star
**The Creative North Star: "The Digital Scholar"**

This design system is built to transform a standard Content Management System into a high-end editorial experience. We are moving away from the "dashboard" aesthetic—cluttered with sidebars and borders—and toward a "Lecture-First" philosophy. The goal is to treat every piece of educational content with the reverence of a prestige print journal.

To break the "template" look, we utilize **Intentional Asymmetry** and **Tonal Layering**. By centering the reading experience within a 720px column and surrounding it with expansive white space, we create a focused, academic environment. The system favors vertical rhythm over horizontal density, ensuring the user’s cognitive load remains low and their focus remains entirely on the pedagogy.

---

## 2. Colors & Surface Philosophy

### The Tonal Palette
The palette is rooted in warm neutrals and academic blues. We avoid pure blacks and harsh whites to reduce eye strain during long-form reading.

*   **Background (`#FAFAF9`):** Our foundational canvas. It mimics high-quality paper.
*   **Surface (`#FFFFFF`):** Reserved for elevated content containers and floating elements.
*   **Primary (`#2563EB` / `primary_container`):** Used sparingly as an "authoritative spark"—hints of intellectual energy.
*   **On-Surface (`#1C1917`):** High-contrast text for maximum legibility.

### The "No-Line" Rule
Standard 1px solid borders are strictly prohibited for sectioning content. To define boundaries, designers must use **Background Color Shifts**. 
*   *Example:* A `surface_container_low` section sitting on a `surface` background creates a clear but soft structural break without the visual "noise" of a stroke.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers. Use the `surface_container` tiers to create depth:
1.  **Level 0 (Base):** `background` (#FAFAF9).
2.  **Level 1 (Sections):** `surface_container_low`.
3.  **Level 2 (Cards/Modules):** `surface` (#FFFFFF).
4.  **Level 3 (Floating/Active):** `surface_bright` with Glassmorphism.

### The "Glass & Signature" Rule
For the sticky navigation and floating overlays, use **Glassmorphism**: `surface` color at 80% opacity with a `20px` backdrop-blur. To add a signature professional polish, main CTAs should utilize a subtle gradient transitioning from `primary` (#2563EB) to `primary_container`.

---

## 3. Typography: The Editorial Voice

The typography scale is designed to create a clear "Information Architecture" through contrast. We pair a sophisticated serif for displays with a highly legible sans-serif for utility.

*   **Display (`DM Serif Display`, 56px/36px, Weight 400):** Our "Editorial Voice." Used for page titles and major chapter breaks. It should feel dominant and intentional.
*   **Headings (`DM Sans`, 28px, Weight 700):** Used for structural sub-headings within a lecture.
*   **Body (`DM Sans`, 18px/16px, Weight 400):** The workhorse. Set with generous line-height (1.6x) to ensure a comfortable academic reading pace.
*   **Labels/Captions (`DM Sans`, 14px, Weight 500):** Used for metadata, figure captions, and secondary UI elements.
*   **Code (`JetBrains Mono`, 14px):** Reserved for technical snippets, providing a distinct "functional" texture.

---

## 4. Elevation & Depth

### The Layering Principle
Depth is achieved through **Tonal Layering** rather than structural lines. By stacking a `surface_container_lowest` card on a `surface_container_low` section, we create a natural lift.

### Ambient Shadows
When an element must float (e.g., a modal or a primary action button), use **Ambient Shadows**:
*   `shadow-subtle`: `0 2px 10px rgba(28, 25, 23, 0.05)` — Note the use of the text color (`#1C1917`) in the shadow rather than pure grey to keep the lighting natural.
*   `glow`: `0 0 40px rgba(37, 99, 235, 0.08)` — Use this only for active states or critical focus points.

### The "Ghost Border" Fallback
If a border is required for accessibility, use a **Ghost Border**: `outline_variant` (#C3C6D7) at **15% opacity**. Never use 100% opaque borders.

---

## 5. Components

### Buttons
*   **Primary:** Full-round (`9999px`), `primary` background. Used only for the "Single Source of Truth" action on a page.
*   **Secondary:** `default` radius (8px), `surface` background with a Ghost Border.
*   **Tertiary:** Text-only with an animated underline on hover (2px height, `accent-soft`).

### Cards & Lists
*   **Rule:** Forbid the use of divider lines.
*   Use `spacing-8` (2.75rem) to separate list items or subtle background shifts (`surface_container_low`) to define card boundaries.
*   **Radii:** Cards must use `xl` (1.5rem / 24px) to feel soft and premium.

### Code Blocks
*   Styled with `surface_container_highest`. 
*   Must include a **Filename Label** in the top-right corner using `label-sm` and `JetBrains Mono`.

### Editorial Hero
*   A specific component for lecture starts. 
*   Features a `display-lg` title, a `64px` vertical gap, and a discrete `accent` line (2px width) to the left of the introductory paragraph.

---

## 6. Do's and Don'ts

### Do
*   **Do** embrace verticality. Let the user scroll through a single, elegant flow.
*   **Do** use `section-y` (96px) spacing to let the content breathe.
*   **Do** use `backdrop-blur` on the sticky navigation to maintain a sense of context.
*   **Do** use `translateY(10px)` scroll reveals for a "rising" content effect.

### Don't
*   **Don't** use sidebars for primary navigation. Keep the reading area centered at 720px.
*   **Don't** use "Alert Red" for errors unless critical; prefer `error_container` with `on_error_container` text for a softer academic tone.
*   **Don't** use standard shadows. If it looks like a "Material Design" drop shadow, it is too heavy.
*   **Don't** crowd elements. If in doubt, increase the spacing by one tier on the scale.