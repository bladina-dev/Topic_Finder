# Phase F4: Polish — Responsive, Animations, Error States

This phase polishes the dashboard for a premium feel.

## Instructions for Claude Code

Work in the frontend/ directory. All 5 pages and components are built. This phase adds visual polish, responsive design, and error handling. Do not change any functionality — only visual and UX improvements.

---

## 1. Responsive Design

Update globals.css with media queries.

At 1200px and below: sidebar collapses to icon-only mode (60px wide), show tooltip on hover with page name. Main content area expands.

At 768px and below: sidebar moves to bottom as a horizontal tab bar (fixed bottom, 60px height). Show only icons. Main content is full-width with padding reduced.

TrendTable: horizontal scroll on mobile with sticky first column (title).

Cards: single column layout on mobile instead of grid.

## 2. Micro-animations

Add CSS transitions and animations:

Page transitions: fade-in when navigating between pages. Use CSS opacity + transform translateY(10px) with 200ms ease-out.

Card hover: subtle scale(1.01) and border glow on trend cards and angle cards.

Button press: scale(0.97) on :active state.

Badge pulse: subtle pulse animation on "HOT" badges (jack_potential >= 0.85).

Loading skeleton: gradient shimmer animation for loading states (before data arrives). Use @keyframes shimmer with background linear-gradient moving left to right.

Sidebar active indicator: sliding highlight bar that animates between navigation items.

Toast notifications: slide in from top-right, auto-dismiss after 3 seconds with fade-out.

## 3. Error States

Add error boundary component at frontend/src/components/ErrorBoundary.jsx — catches React errors and shows a friendly "Something went wrong" message with a retry button.

For each page: if the API call fails, show an inline error card with the error message, a retry button, and a subtle red background. Don't crash the page.

Network error detection: if fetchHealth fails on mount, show a persistent banner at the top "Cannot connect to API server. Is it running on port 8000?" with a retry button.

Empty states for each page: Discovery — "No topics discovered yet", Angles — "Generate your first content angles", Sources — "No source files found", Brand — "Upload a brand strategy PDF", Settings — all healthy.

## 4. Typography and Spacing

Review all text sizes and spacing for consistency. Headings: page titles 1.5rem semibold, section titles 1.1rem medium, card titles 1rem medium. Body text: 0.9rem regular. Meta text: 0.8rem with text-secondary color.

Consistent spacing: use CSS custom properties throughout. --space-xs: 0.25rem, --space-sm: 0.5rem, --space-md: 1rem, --space-lg: 1.5rem, --space-xl: 2rem, --space-2xl: 3rem.

## 5. Dark Theme Refinement

Add subtle gradient backgrounds to page sections. Use very subtle noise texture (CSS radial-gradient with dots) on the main background. Ensure all text passes WCAG AA contrast ratio. Add a subtle box-shadow on the sidebar to separate it from content.

---

## Verification

Run cd frontend && npm run dev. Test at different viewport widths:
1. Desktop (1440px) — full sidebar, grid layouts
2. Tablet (1024px) — collapsed sidebar with icons
3. Mobile (375px) — bottom tab bar, single column
4. Navigate between all pages — verify fade-in transitions
5. Trigger an error (stop the API server) — verify error states show
6. Check loading states — verify skeleton shimmer
7. No console errors or warnings
