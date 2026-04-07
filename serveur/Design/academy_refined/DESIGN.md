# Design System Document: The Scholastic Atelier

## 1. Overview & Creative North Star: "The Mindful Curator"
In the high-pressure environment of education, data should never feel like a burden. Our Creative North Star, **"The Mindful Curator,"** moves away from the cold, "engine-room" aesthetic of traditional dashboards toward a high-end, editorial experience. 

This system rejects the rigid, boxy constraints of legacy school software. Instead, we use **intentional asymmetry, expansive breathing room, and soft tonal layering** to guide a teacher’s eye. The goal is to make complex student data feel like a curated gallery of insights—sophisticated, calm, and authoritative. We break the "template" look by using exaggerated typographic scales and overlapping surface elements that create a sense of physical depth.

---

## 2. Colors: Tonal Atmosphere
We move beyond "functional" color into "atmospheric" color. The palette is a sophisticated blend of deep slate blues and sea-foam greens, designed to reduce cognitive fatigue.

### The "No-Line" Rule
**Borders are strictly prohibited for sectioning.** To define boundaries, you must use background color shifts. For example, a `surface-container-low` data panel should sit on a `surface` background. The transition between these two shades is the boundary.

### Surface Hierarchy & Nesting
Treat the UI as a series of nested, physical layers.
*   **Base:** `surface` (#f7faf9)
*   **Secondary Sections:** `surface-container-low` (#f0f5f4)
*   **Interactive Cards:** `surface-container-lowest` (#ffffff) for a "lifted" feel.
*   **Utility Panels:** `surface-container-high` (#e2eae9) for drawers or sidebars.

### The Glass & Gradient Rule
To elevate the experience, floating elements (like hover-state tooltips or dropdowns) should use **Glassmorphism**. Combine `surface-container-lowest` at 80% opacity with a `backdrop-blur` of 12px. Main CTAs should use a subtle linear gradient: `primary` (#32657a) to `primary_dim` (#24596e) at a 135-degree angle to provide a "jeweled" depth.

---

## 3. Typography: The Editorial Voice
We use a dual-typeface system to balance authority with high readability.

*   **Display & Headlines (Manrope):** This geometric sans-serif provides a modern, architectural feel. Use `display-lg` (3.5rem) for high-level student performance metrics to create an editorial "hero" moment.
*   **Body & Labels (Public Sans):** A neutral, highly legible face optimized for dense data. 
*   **Hierarchy as Navigation:** Large `headline-sm` titles should be used to anchor pages, paired with `body-md` for descriptive metadata. The contrast between the bold Manrope and the functional Public Sans creates a signature, "custom-built" look.

---

## 4. Elevation & Depth: Tonal Layering
Traditional drop shadows and heavy borders are replaced by light and tone.

*   **The Layering Principle:** Depth is achieved by "stacking." Place a `surface-container-lowest` card on a `surface-container` background to create a soft, natural lift.
*   **Ambient Shadows:** For floating elements (Modals/Popovers), use an extra-diffused shadow: `offset: 0, 20px`, `blur: 40px`, `color: rgba(44, 52, 52, 0.06)`. The tint is derived from `on-surface` (#2c3434) to feel like natural light.
*   **The "Ghost Border":** If a separator is required for accessibility, use `outline-variant` (#abb4b3) at **15% opacity**. It should be felt, not seen.

---

## 5. Components: Intentional Primitives

### Data Cards & Tables
*   **The Card:** Use `rounded-xl` (0.75rem) corners. Forbid the use of divider lines. Separate header and content using a `12` (2.75rem) spacing unit of vertical white space.
*   **The Table:** Row separation must be achieved through alternating row colors (Zebra striping) using `surface` and `surface-container-low`. Forbid vertical grid lines.

### Interactive Elements
*   **Buttons:** 
    *   *Primary:* `primary` background, `on-primary` text, `rounded-lg`.
    *   *Tertiary (Ghost):* No background. Use `primary` text. On hover, apply a `primary-container` (#b1e4fd) background at 40% opacity.
*   **Chips:** Used for student tags or filters. Use `secondary-container` (#c4ebd9) with `on-secondary-container` (#35594b) text. Shape should be `rounded-full`.
*   **Input Fields:** Use `surface-container-highest` for the field background with no border. On focus, transition to a 1px "Ghost Border" of `primary`.

### Data Visualization
Charts should utilize the `tertiary` (#366769) and `secondary` (#426658) ranges to ensure they feel integrated into the "soothing" palette rather than clashing with standard high-vibrancy chart colors.

---

## 6. Do’s and Don’ts

### Do:
*   **Use Asymmetry:** Place a large metric (`display-md`) on the left and a smaller list (`body-md`) on the right to create a sophisticated, non-template layout.
*   **Embrace Negative Space:** Use the `20` (4.5rem) and `24` (5.5rem) spacing scales between major dashboard sections.
*   **Layer Surfaces:** Think of the UI as paper on a desk. Use the `surface-container` tiers to define "importance."

### Don’t:
*   **Don't use 1px solid borders:** Never use a high-contrast line to separate student records or dashboard widgets.
*   **Don't use "True Black":** All dark text must use `on-surface` (#2c3434) to maintain the soft, professional atmosphere.
*   **Don't crowd the view:** If a dashboard feels "busy," increase the padding to the next step in the spacing scale rather than adding lines to organize it.