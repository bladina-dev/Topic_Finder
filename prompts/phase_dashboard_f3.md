# Phase F3: Brand Profile Page + Settings Page

This phase builds the final two pages of the dashboard.

## Instructions for Claude Code

Work in the frontend/ directory. The API client, Router, Sidebar, and other pages are already set up. Add these two page components. Use the existing design system.

---

## Page 1: Brand Profile Page (BrandPage.jsx)

Create frontend/src/pages/BrandPage.jsx.

Two-section layout.

Section 1 — Upload area: a large drag-and-drop zone with dashed border. Accept PDF files only. Show file name and size after selection. Brand name text input (optional). "Upload & Analyze" button. Loading state with progress text "Processing PDF...". On success show a green toast notification with pages processed and chunks stored count.

Section 2 — Brand Profile display: fetched from /api/brands/profile on mount. Render in a grid of styled cards: "Brand Name" card, "Industry" card, "Tone of Voice" card, "Target Audience" card, "Key Messages" card (bulleted list), "Values" card (tag pills), "Competitors" card (tag pills), "Summary" card (paragraph). Each card has a subtle icon and glass-morphism background. If no brand profile exists show an empty state: "Upload a brand strategy PDF to get started."

Action bar: "Clear Brand Data" button with confirmation modal — calls DELETE /api/brands. "Test Query" input with search button — calls GET /api/brands/context?query=... and shows the returned context in a result card.

## Page 2: Settings Page (SettingsPage.jsx)

Create frontend/src/pages/SettingsPage.jsx.

Fetch current settings from GET /api/settings on mount.

Section 1 — API Keys: render a grid of ApiKeyInput components.

Create frontend/src/components/ApiKeyInput.jsx. Each instance shows: a label (e.g. "Tavily API Key"), the service icon/emoji, a password-style input that shows the masked value (****xxxx) from the API, a toggle eye button to show/hide, a status indicator dot (green if the masked value is not empty, red if empty), and a "test" button for keys that support it. When the user types a new value and clicks Save, only the changed keys are sent to POST /api/settings.

API Keys to show: Tavily Search API (tavily_api_key), SerpAPI Google Trends (serpapi_api_key), Google API (google_api_key), YouTube Data API (youtube_data_api_key), Anthropic Claude (anthropic_api_key), Notion API (notion_api_key), Telegram Bot Token (telegram_bot_token), Azure Speech Key (azure_speech_key).

Section 2 — Agent Configuration: form fields for default_ai_provider (dropdown: gemini, claude, lmstudio), agent_timezone (text input), default_sources (text input), youtube_scan_enabled (toggle), influencer_scan_enabled (toggle), google_trends_enabled (toggle).

Section 3 — System Health: on mount call /api/health and display a status card showing: overall status (healthy/unhealthy), version, provider. API connectivity matrix: green/red dots for each configured API (tavily, serpapi, youtube, notion, telegram).

"Save All Settings" button at the bottom that sends all changed values to POST /api/settings. Show a success toast on save.

---

## Verification

Run cd frontend && npm run dev. Open http://localhost:5173.
1. Navigate to /brand — verify upload zone renders
2. Navigate to /settings — verify API keys load with masked values
3. Check health status shows green dots for configured APIs
4. Type a new value in an API key field and save — verify .env updates
5. No console errors
