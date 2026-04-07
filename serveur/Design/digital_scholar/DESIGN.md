# Design System Strategy: The Digital Scholar

## 1. Overview & Creative North Star
The Creative North Star for this design system is **"The Mindful Curator."** 

This is not a traditional software interface; it is a high-end digital atelier. We are moving away from the "app-like" density of SaaS platforms and toward a "Digital Scholar" aesthetic—an editorial-first experience that prioritizes focus, intentionality, and breathing room. 

The system breaks the "template" look by utilizing a strict **720px centered column vertical rhythm**, creating a scholarly, essay-like flow. We reject the rigidity of standard grids in favor of **intentional asymmetry**—where imagery and pull-quotes may bleed slightly out of the central column—and **tonal depth**, where the interface feels like stacked sheets of premium vellum rather than a flat digital screen.

---

## 2. Colors & Surface Philosophy
The palette is grounded in warm neutrals and authoritative blues, designed to reduce eye strain and promote deep work.

### The "No-Line" Rule
**1px solid borders are strictly prohibited for sectioning.** To define boundaries, designers must use **Tonal Layering**. If a section ends, the background color should shift from `surface` (#FFFFFF) to `surface_container_low` (#FAF2EE). This creates a sophisticated, organic transition that mimics natural light and shadow rather than mechanical dividers.

### Surface Hierarchy & Nesting
Treat the UI as a physical stack. Use the `surface-container` tiers to create "nested" depth:
*   **Base:** `background` (#FFF8F5)
*   **Primary Content Area:** `surface` (#FFFFFF)
*   **Low Priority/Navigation:** `surface_container_low` (#FAF2EE)
*   **Interactive Overlays:** `surface_container_highest` (#E9E1DD)

### The "Glass & Gradient" Rule
To ensure the "Curator" feel, use **Glassmorphism** for all floating elements (Nav bars, Tooltips). 
*   **Token:** 80% opacity of `surface`, 20px Backdrop Blur.
*   **Signature Texture:** Use a subtle linear gradient on primary CTAs, transitioning from `primary` (#004AC6) to `primary_container` (#2563EB) at a 135-degree angle. This adds "soul" and a tactile, ink-like quality to the blue.

---

## 3. Typography
Typography is the primary vehicle for the "Digital Scholar" brand. We utilize a high-contrast pairing between a literary Serif and a functional Sans-Serif.

*   **The Display Voice (Newsreader):** Used for `display`, `headline`, and `title-lg`. This serif face conveys authority and history. It should be typeset with tighter letter-spacing (-2%) to feel like a premium broadsheet.
*   **The Utility Voice (Plus Jakarta Sans):** Used for `body`, `labels`, and `title-sm`. This sans-serif provides modern clarity.
*   **The Golden Ratio of Reading:** All body text must maintain a **1.6x line-height**. This generous spacing ensures that long-form scholarship remains legible and unhurried.

---

## 4. Elevation & Depth
Depth is achieved through "stacking" rather than traditional structural lines.

*   **The Layering Principle:** Place a `surface_container_lowest` (#FFFFFF) card on a `surface_container_low` (#FAF2EE) background to create a soft, natural lift.
*   **Ambient Shadows:** When an element must float (e.g., a modal), use an ultra-diffused shadow:
    *   `Y: 20px, Blur: 40px, Color: on_surface (1C1917) at 4% opacity`.
    *   This mimics ambient environmental light rather than a harsh digital drop shadow.
*   **The "Ghost Border" Fallback:** If a border is required for accessibility (e.g., input fields), use the `outline_variant` token at **10% opacity**. Never use 100% opaque borders.

---

## 5. Components

### Buttons
*   **Primary:** Full-round (`9999px`), Gradient fill (Primary to Primary-Container), `on_primary` text.
*   **Secondary:** 8px (`sm`) radius, `surface_container_high` background, `primary` text.
*   **Tertiary:** No background. Underline on hover using a 2px `surface_tint` offset.

### Cards & Content Modules
*   **Radius:** 24px (`xl`).
*   **Separation:** **Forbid divider lines.** Use `16` (5.5rem) or `20` (7rem) spacing tokens to separate content modules.
*   **Interaction:** On hover, a card should shift from `surface` to `surface_bright` with a 4% ambient shadow.

### Input Fields
*   **Styling:** 8px radius. Background: `surface_container_lowest`. 
*   **Focus State:** Shift background to `surface` and apply a 1px "Ghost Border" (20% `primary`). No heavy outer glows.

### Selection & Chips
*   **Filter Chips:** Full-round (`9999px`). Use `surface_container_high` for unselected and `primary` for selected. 

---

## 6. Do’s and Don’ts

### Do
*   **Center the Focus:** Keep the main content within the 720px column to simulate the experience of reading a book.
*   **Embrace White Space:** Use the `20` (7rem) and `24` (8.5rem) spacing tokens between major sections to let the "Scholar" breathe.
*   **Use Tonal Shifts:** If a piece of content feels "lost," change the background color of its container by one tier rather than adding a border.

### Don’t
*   **No "App" Density:** Avoid multi-column layouts that cram information. The Scholar is mindful, not overwhelmed.
*   **No Grey Shadows:** Never use pure #000000 for shadows. Always tint shadows with the `on_surface` color to maintain the warm, organic palette.
*   **No Default Corners:** Avoid the "medium" 4px-12px range for primary actions. Either go full-round (Primary) or distinct 24px (Cards) to maintain a signature look.

### Accessibility Note
While we use tonal layering, ensure that the contrast between `surface` and `surface_container` tiers meets a minimum 3:1 ratio for structural visibility, and all text maintains a 4.5:1 ratio against its respective background tier.