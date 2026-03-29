# Phase F1: Router + Sidebar + Discovery Page

This phase sets up the frontend foundation: React Router, sidebar navigation, and the Topic Discovery page.

## Instructions for Claude Code

Work in the frontend/ directory. Install react-router-dom: cd frontend && npm install react-router-dom. Rewrite the frontend structure. Keep the existing dark theme from styles/globals.css as the foundation but extend it significantly. Run npm run dev at the end to verify it builds and renders.

---

## Step 1: API Client

Create frontend/src/api.js with a centralized API client. Export async functions for every endpoint:

- fetchHealth() — GET /api/health
- scanTrends(mock, maxResults, sources) — GET /api/scan?mock=...&max_results=...&sources=...
- generateAngles(mock, maxTrends, anglesPerTrend, sources) — POST /api/angles/generate
- fetchSources() — GET /api/sources
- fetchSourceEntries(name) — GET /api/sources/{name}
- addSourceEntry(name, entry) — POST /api/sources/{name}/add
- fetchSeedKeywords(name) — GET /api/sources/{name}/seeds
- fetchSettings() — GET /api/settings
- updateSettings(updates) — POST /api/settings
- fetchBrandProfile() — GET /api/brands/profile
- uploadBrandPdf(file, brandName) — POST /api/brands/upload (multipart/form-data)
- clearBrandData() — DELETE /api/brands
- updateAngleStatus(filenameStem, status) — POST /api/angles/status

Use const API_BASE = "/api" at the top. Each function should handle errors and throw with a readable message.

## Step 2: App Shell with Router

Rewrite frontend/src/App.jsx. Import BrowserRouter, Routes, Route from react-router-dom. Create a layout with a fixed left Sidebar and a main content area. Define routes: "/" for DiscoveryPage, "/angles" for AnglesPage, "/sources" for SourcesPage, "/brand" for BrandPage, "/settings" for SettingsPage.

## Step 3: Sidebar Component

Create frontend/src/components/Sidebar.jsx. Fixed left sidebar, 260px wide, dark background (#0a0a0f). Navigation items with icons: 🔍 Discovery (link to /), ✍️ Content Angles (/angles), 📋 Sources (/sources), 📄 Brand Profile (/brand), ⚙️ Settings (/settings). Active item highlighted with a gradient accent. At the bottom show a small health indicator that calls fetchHealth() on mount and shows green dot if healthy, red if not. Logo/title at the top: "Marketing Agent" with a ⚡ icon.

## Step 4: Discovery Page

Create frontend/src/pages/DiscoveryPage.jsx. This is the main page.

Header area with title "Topic Discovery" and subtitle showing last scan time.

Controls bar with: Source selector dropdown (fetches available sources from /api/sources on mount, defaults to "saudi_general"). Mock/Live toggle switch. "Scan Now" button with loading spinner. Max results number input (default 15).

Results section: render a TrendTable component.

Create frontend/src/components/TrendTable.jsx. A styled table with columns: #, Title, Source (colored badge), Origin (TREND/INFLUENCER/SEED_KEYWORD badge), Jack Score (progress bar with color: green >=0.8, yellow >=0.6, red <0.6), Published (relative time), Link (external link icon). Sortable by clicking column headers (default sort by jack_potential desc). Filter row above the table with source type dropdown and origin layer dropdown.

Empty state: show a centered illustration with text "Click Scan Now to discover trending topics".

## Step 5: Styling

Extend frontend/src/styles/globals.css with the new component styles. Design system:

Colors: --bg-primary: #0a0a0f, --bg-secondary: #111118, --bg-card: #16161f, --bg-hover: #1e1e2a, --accent-primary: #6366f1 (indigo), --accent-secondary: #8b5cf6 (purple), --text-primary: #e5e5e5, --text-secondary: #888, --success: #22c55e, --warning: #f59e0b, --error: #ef4444.

Typography: Import Inter from Google Fonts. Use it as the default font.

Sidebar: fixed position, full height, with subtle border-right.

Cards: glass-morphism effect with backdrop-filter blur, subtle border.

Badges: colored pill-shaped badges for source types. youtube=red, targeted=blue, serp_trends=purple, influencer=orange, seed_keyword=green, gulf_news=cyan, twitter_ksa=sky.

Buttons: gradient primary button with hover scale effect. Ghost secondary button.

Table: alternating row backgrounds, hover highlight, sticky header.

Loading: pulsing gradient skeleton and spinning indicator.

---

## Verification

Run cd frontend && npm run dev. Open http://localhost:5173. Verify:
1. Sidebar renders with all 5 navigation items
2. Discovery page shows with controls bar
3. Clicking "Scan Now (Mock)" fetches from API and populates table
4. Table shows colored badges and jack score bars
5. No console errors
