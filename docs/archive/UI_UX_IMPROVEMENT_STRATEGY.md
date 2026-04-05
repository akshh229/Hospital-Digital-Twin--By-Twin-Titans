# 🎨 Project Lazarus: UI/UX Improvement Strategy

Based on the `ui-ux-designer` skill guidelines and your current `FRONTEND_FOUNDATION_COMPLETE.md`, here is a comprehensive plan to elevate the user interface and user experience of your clinical dashboard. 

In a medical context, design isn't just about aesthetics; it's about reducing cognitive load, preventing errors, and surfacing critical information instantly.

## 1. Accessibility & Inclusive Design (WCAG 2.1 AAA)
Clinical dashboards must be universally accessible, especially under high-stress situations or long shifts.
- **Colorblind-Safe Alerts:** Relying purely on color (`#ef4444` for Critical, `#f59e0b` for Warning) is a major risk in clinical environments. Always pair status colors with **distinct iconography** (e.g., an 🛑 Octagon/Cross for Critical alerts, a ⚠️ Triangle for Warnings, and a ✅ Circle for Normal). 
- **Contrast Ratios:** The light clinical palette should still maintain at least **7:1** contrast on critical text, labels, and telemetry values so the dashboard stays readable during long clinical reviews and live demos.
- **Screen Reader Support:** Add `aria-live="assertive"` regions to your `AlertBanner` component. This ensures that when a real-time WebSocket alert is broadcasted, medical professionals using screen readers are immediately and proactively notified.

## 2. Typography & Data Presentation
Data precision is critical. You've correctly chosen `Inter` for UI text and `JetBrains Mono` for vitals. Let's optimize their use:
- **Tabular Numerals:** Ensure that `font-variant-numeric: tabular-nums;` is applied in CSS to all vitals displaying in `JetBrains Mono`. This forces numbers to be equal width, preventing text elements from shifting horizontally as data rapidly updates via WebSockets.
- **Label Hierarchy:** Use uppercase, tracked-out text (e.g., in Tailwind: `text-xs uppercase tracking-wider text-muted`) for vital sign labels (e.g., "HEART RATE"), keeping the high-contrast `Text` color reserved exclusively for the actual values.

## 3. Information Architecture & Progressive Disclosure
A 4-panel dashboard can become visually overwhelming if every panel displays maximum detail all at once. 
- **Progressive Disclosure:** In the `PatientCard` component, display only top-level essentials: Heart Rate, O2 Saturation, current status, and a minimal sparkline. Users must actively click the card to enter the `PatientDetail` view, which then reveals complex, interactive `Recharts` data and the `PharmacyTable`.
- **Visual Hierarchy:** Use layout positioning to guide the eye. The `AlertBanner` should take absolute precedence fixed at the top of the interface, followed immediately by unstable/critical patients, and stable patients at the end.

## 4. Interaction Design & State Management
- **Reassuring Loading States:** When WebSocket data is pending or reconnecting, use **skeleton loaders** with a subtle pulse. Never show a blank chart or an empty state without context, as this could be misconstrued as a missing patient or a flatline. Display a clear "Connecting to telemetry..." overlay.
- **Micro-Animations:** Use subtle background flashes or border color transitions when a vital sign crosses a threshold. Because you are using a debounced alert engine on the backend, the UI should reflect this stability by animating smoothly between states rather than flickering.

## 5. Design System Standardization
- **Strict Tokenization:** In your Tailwind configuration (`tailwind.config.js`), enforce the use of your semantic colors (e.g., `bg-surface`, `text-critical`, `border-muted`) rather than raw utilities (like `bg-red-500`). This ensures that if the hospital requests a contrast tweak later, changing a single hex code instantly fixes the entire app.
- **Component Reusability:** Define standard clinical container classes. For example, use a reusable dossier-style panel with soft borders, pale surfaces, and consistent padding so the interface feels premium without drifting into a generic dark dashboard look.

---
### 🎯 Recommended First Step
Before building complex charts, finalize your Design Tokens in `tailwind.config.js` and build the foundational `PatientCard` showcasing the "Normal", "Warning", and "Critical" color-and-icon combinations.
