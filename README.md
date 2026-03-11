# Autonomous Marketing Agent

An AI-powered marketing agent designed to monitor current trends, analyze brand psychology, and generate highly targeted, culturally relevant content angles (with a specific focus on the Saudi/Gulf market).

## Features
- **Trend Scanning:** Integrates with Tavily to fetch real-time topics and hashtags in Saudi Arabia and the Gulf region.
- **Psychological Triggers:** Applies deep cognitive triggers (FOMO, Zeigarnik effect, Curiosity gap, Loss Aversion, Social Proof, and Gain) tailored for sophisticated local audiences.
- **Cultural Resonance:** Automatically injects local calendar events (e.g., Ramadan, Eid, Riyadh Season) into the ideation process.
- **Benchmarking Engine:** Built-in quality assurance script (`run_benchmark.py`) that judges the creative novelty, hook power, brand alignment, and cultural relevance using an AI judge (Google Gemini).

## Installation

This project is managed using `uv` for lightning-fast dependency resolution and virtual environments.

### Option 1: Using UV (Recommended)
1. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Sync the project: `uv sync`
3. Enter the environment: `uv run python run_benchmark.py --mode mock`

### Option 2: Using standard pip
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

The application requires specific API keys to function securely. Create your `.env` file from the example:
```bash
cp .env.example .env
```

And configure:
```env
GOOGLE_API_KEY="your-gemini-key"
TAVILY_API_KEY="your-tavily-key"
```
*Note: The project uses Gemini (`gemini-2.5-flash`) for AI judging and generation.*

## Running the Application

### The Benchmark Engine
To evaluate the quality of the generated angles:

```bash
# Run with mock data (to test scoring heuristics without API calls)
uv run python run_benchmark.py --mode mock --no-judge

# Run live with Tavily and Gemini AI Judge
uv run python run_benchmark.py --mode live --trends 4 --angles 3 
```

The benchmark evaluates angles across 6 dimensions and generates a comprehensive terminal report and JSON dump of the results.

## Project Structure
- `src/benchmark.py`: Core logic for grading generation quality and filtering clichés.
- `src/psychology.py`: Defines the psychology templates (Open Loop, Gain, Loss, etc.) with explicit rules and Gulf right/wrong examples.
- `src/ai_orchestrator.py`: Prompt construction, AI provider routing, and cultural parameter injection.
- `src/trend_scanner.py`: Searches the web via Tavily to harvest current hashtags and topics.
- `run_benchmark.py`: Entrypoint for QA testing and iterating on prompt improvements.

## Roadmap (V2 Features)
- **Automated Scheduling:** Implement a daily trigger (e.g., 6:00 AM/PM) via GitHub Actions or a local Cron job so the agent runs autonomously without manual terminal commands.
- **Direct Delivery Pipeline:** Automatically push the generated, 50+ score angles directly to the marketing team via WhatsApp, Telegram, or Email for immediate review and posting.
- **Predictive Scoring & Dark Social Integration:** (See V2 Features documentation for full list of upcoming upgrades).
