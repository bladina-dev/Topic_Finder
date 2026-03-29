# Phase F2: Content Angles Page + Source Manager Page

This phase builds two new pages for the dashboard.

## Instructions for Claude Code

Work in the frontend/ directory. The API client (api.js), Router (App.jsx), and Sidebar are already set up from Phase F1. Add the two new page components and their sub-components. Use the existing design system from globals.css.

---

## Page 1: Content Angles Page (AnglesPage.jsx)

Create frontend/src/pages/AnglesPage.jsx.

Header area: title "Content Angles" with subtitle "Generate AI-powered content ideas with psychological triggers".

Controls bar: same source selector as Discovery Page. AI Provider dropdown (gemini, claude, lmstudio). Angles per trend number input (default 3). Max trends number input (default 8). Mock/Live toggle. "Generate Angles" button with loading state — this calls generateAngles from api.js.

Results section: when output is received, render each TrendWithAngles result as an expandable section. The trend header shows title, source badge, jack score, and an expand/collapse chevron. Default collapsed after first 3.

For each angle inside a trend, create an AngleCard component at frontend/src/components/AngleCard.jsx (rewrite the existing one). Each card shows: headline as the card title, hook as an italic blockquote, body_outline as a numbered list, platform badge (Twitter=blue, LinkedIn=indigo, Instagram=pink, TikTok=black, General=gray), psych_triggers as colored pill badges (FOMO=red, curiosity_gap=purple, zeigarnik=orange, social_proof=green, gain=emerald, loss_aversion=amber), brand_alignment_score as a circular percentage gauge.

Action buttons on each angle card: "✅ Approve" and "❌ Skip" — these call updateAngleStatus via API. "📋 Copy" — copies the headline + hook to clipboard. Visual feedback on button click (brief color flash).

Stats bar at the top when results exist: total trends, total angles, provider used, average brand alignment score.

Export bar at bottom: "Download JSON" button, "Download Markdown" button (just download the raw API response as .json or format as .md client-side).

## Page 2: Source Manager Page (SourcesPage.jsx)

Create frontend/src/pages/SourcesPage.jsx.

Two-panel layout. Left panel (300px): list of source files fetched from /api/sources. Each item shows name and entry count. Click to select and load entries in right panel. Highlight the active source.

Right panel: SourceEditor component.

Create frontend/src/components/SourceEditor.jsx. Shows a table of entries for the selected source file: columns vertical, type, handle_or_domain, label, youtube_handle. Each row is read-only (editing CSV inline is scope creep for MVP).

Add source form below the table: vertical dropdown (tech, finance, lifestyle, food, media, ecommerce, government, culture, sports, general), type dropdown (domain, twitter, instagram, tiktok, youtube), handle_or_domain text input, label text input. "Add Source" button that calls addSourceEntry via API, then refreshes the list.

Seed Keywords tab: if the selected source is "seed_keywords", render a different view. Show a table with columns: vertical, keyword, intent, label. Fetched from /api/sources/{name}/seeds.

Entry count badge on each source in the left panel.

---

## Verification

Run cd frontend && npm run dev. Open http://localhost:5173.
1. Navigate to /angles — verify controls render
2. Click Generate (Mock) — verify angle cards appear with psych trigger badges
3. Navigate to /sources — verify source list loads in left panel
4. Click "saudi_general" — verify entries table loads
5. Add a test source entry — verify it appears in the table
6. No console errors
