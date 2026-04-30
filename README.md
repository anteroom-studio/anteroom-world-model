# Anteroom World Model

**Macro intelligence research system for historical market pattern analysis.**

Anteroom World Model is a Python-based research prototype that collects long-range financial and macroeconomic datasets, compares current market conditions against historical stress periods, and produces structured scenario analysis for research review.

> Built by **Anteroom Studio** as part of its private research and intelligence tooling.

---

## Overview

Most market tools focus on a single chart, asset, or headline stream. Anteroom World Model takes a wider systems view by combining historical macro data, live market indicators, cross-asset relationships, and crisis-pattern comparisons.

The system is designed to help answer questions like:

- Which historical periods share similar conditions with the current market?
- Which indicators tend to lead or lag other indicators?
- What risk signals are becoming more or less important?
- How do equities, commodities, rates, currencies, and crypto behave across similar regimes?

This is a research tool, not a trading signal service.

---

## Core Capabilities

- Historical data collection from public market and macro sources
- Cross-asset correlation analysis
- Lead-lag relationship detection
- Historical crisis pattern comparison
- Live market snapshot generation
- Optional model-assisted scenario summaries
- Terminal dashboard for monitoring current outputs

---

## System Flow

```text
Historical Data + Live Market Data
              ↓
Data Normalization
              ↓
Correlation Engine
              ↓
Lead/Lag Analysis
              ↓
Historical Pattern Matching
              ↓
Scenario Summary
              ↓
Terminal Dashboard
```

---

## Data Sources

| Source | Coverage |
|---|---|
| FRED | Inflation, rates, GDP, unemployment, treasury data |
| Yahoo Finance | Equities, commodities, VIX, dollar index |
| CoinGecko | Crypto market data |
| World Bank | Global GDP and macroeconomic data |

---

## Requirements

- Python 3.8+
- 8GB RAM recommended
- Around 2GB+ storage for downloaded datasets
- Optional Anthropic API key for model-assisted summaries

---

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local environment file:

```bash
cp .env.example .env
```

Add your local key only if you want model-assisted summaries:

```env
ANTHROPIC_API_KEY=your_key_here
```

Never commit `.env` or real credentials.

---

## Usage

Download historical data:

```bash
python data_collector.py
```

Run analysis:

```bash
python correlation_engine.py
```

Launch dashboard:

```bash
python dashboard.py
```

---

## Project Structure

| File | Purpose |
|---|---|
| `config.py` | Runtime settings and environment loading |
| `data_collector.py` | Downloads and updates market/macro datasets |
| `correlation_engine.py` | Runs correlation, lead-lag, and historical pattern analysis |
| `dashboard.py` | Displays live market data and latest analysis in terminal |
| `.env.example` | Safe local configuration template |
| `.gitignore` | Keeps local data, caches, and secrets out of Git |

---

## Safety and Scope

Anteroom World Model is built for research, education, and internal experimentation. Outputs may be incomplete, stale, or incorrect depending on source availability, market conditions, and local configuration.

This project does not provide financial, investment, legal, or professional advice. Always verify outputs independently before using them in any real-world decision.

---

## Studio

**Anteroom Studio**  
Research systems, intelligence interfaces, and experimental software.
