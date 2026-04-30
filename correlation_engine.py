"""
Anteroom World Model - Correlation and Pattern Engine

Runs cross-asset correlation analysis, lead-lag detection, historical stress-period
comparison, and optional model-assisted scenario summaries.
"""

import os
import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from config import DATA_PATH, ANTHROPIC_KEY


KNOWN_CRASHES = {
    "Great Depression 1929": ("1928-01-01", "1933-01-01"),
    "Oil Crisis 1973": ("1972-01-01", "1975-01-01"),
    "Black Monday 1987": ("1987-06-01", "1988-06-01"),
    "Dot-com Crash 2000": ("1999-01-01", "2002-12-01"),
    "Financial Crisis 2008": ("2007-01-01", "2009-12-01"),
    "COVID Crash 2020": ("2020-01-01", "2020-12-01"),
    "Crypto Crash 2022": ("2021-11-01", "2022-12-01"),
}


def load_all_data():
    """Load every downloaded CSV series from the historical data folder."""
    data = {}
    historical_path = f"{DATA_PATH}/historical"

    if not os.path.exists(historical_path):
        print("❌ Historical data not found. Run: python data_collector.py")
        return {}

    for file in os.listdir(historical_path):
        if file.endswith(".csv"):
            name = file.replace(".csv", "")
            try:
                df = pd.read_csv(f"{historical_path}/{file}", parse_dates=["date"])
                df = df.sort_values("date").set_index("date")
                data[name] = df["value"]
                print(f"  ✅ Loaded {name}: {len(df)} records")
            except Exception as exc:
                print(f"  ❌ {name}: {exc}")

    return data


def merge_data(data_dict):
    """Merge all available series into one weekly time-indexed DataFrame."""
    if not data_dict:
        return pd.DataFrame()

    data_dict = {key: value for key, value in data_dict.items() if len(value) > 0}
    df = pd.DataFrame(data_dict)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df.resample("W").last().ffill()


def find_correlations(df):
    """Calculate cross-asset correlations using four-week percentage changes."""
    if df.empty:
        return {}

    pct = df.pct_change(4)
    corr_matrix = pct.corr()
    correlations = {}
    cols = corr_matrix.columns.tolist()

    for index, col1 in enumerate(cols):
        for col2 in cols[index + 1:]:
            corr = corr_matrix.loc[col1, col2]
            if not np.isnan(corr):
                correlations[f"{col1}_vs_{col2}"] = round(corr, 3)

    return dict(sorted(correlations.items(), key=lambda item: abs(item[1]), reverse=True))


def find_lead_lag_relationships(df, max_lag_weeks=12):
    """Identify indicators that historically move before other indicators."""
    relationships = []
    cols = df.columns.tolist()
    pct = df.pct_change(4)

    for leader in cols:
        for follower in cols:
            if leader == follower:
                continue

            best_corr = 0
            best_lag = 0

            for lag in range(1, max_lag_weeks + 1):
                try:
                    corr = pct[leader].corr(pct[follower].shift(-lag))
                    if abs(corr) > abs(best_corr):
                        best_corr = corr
                        best_lag = lag
                except Exception:
                    continue

            if abs(best_corr) > 0.4:
                relationships.append({
                    "leader": leader,
                    "follower": follower,
                    "lag_weeks": best_lag,
                    "correlation": round(best_corr, 3),
                    "direction": "same" if best_corr > 0 else "opposite",
                })

    relationships.sort(key=lambda item: abs(item["correlation"]), reverse=True)
    return relationships[:50]


def extract_crash_patterns(df):
    """Extract six-month pre-event conditions for known historical stress periods."""
    patterns = {}

    for crash_name, (start, _end) in KNOWN_CRASHES.items():
        try:
            pre_start = pd.to_datetime(start) - timedelta(weeks=26)
            pre_end = pd.to_datetime(start)
            pre_crash = df.loc[pre_start:pre_end]

            if pre_crash.empty:
                continue

            pattern = {"crash": crash_name, "period": start}
            for col in df.columns:
                if col in pre_crash.columns:
                    series = pre_crash[col].dropna()
                    if len(series) > 4:
                        total_change = ((series.iloc[-1] - series.iloc[0]) / abs(series.iloc[0])) * 100
                        pattern[f"{col}_change_pct"] = round(total_change, 2)

            patterns[crash_name] = pattern
        except Exception:
            continue

    return patterns


def compare_current_to_history(df, crash_patterns):
    """Compare recent conditions with historical stress-period patterns."""
    if df.empty or not crash_patterns:
        return []

    six_months_ago = datetime.now() - timedelta(weeks=26)
    current = df.loc[six_months_ago:]

    if current.empty:
        return []

    current_changes = {}
    for col in df.columns:
        if col in current.columns:
            series = current[col].dropna()
            if len(series) > 2:
                change = ((series.iloc[-1] - series.iloc[0]) / abs(series.iloc[0])) * 100
                current_changes[col] = round(change, 2)

    similarities = []
    for crash_name, pattern in crash_patterns.items():
        score = 0
        matches = 0
        details = []

        for col, curr_val in current_changes.items():
            hist_key = f"{col}_change_pct"
            if hist_key in pattern:
                hist_val = pattern[hist_key]
                if (curr_val > 0 and hist_val > 0) or (curr_val < 0 and hist_val < 0):
                    score += 1
                    matches += 1
                    details.append(f"{col}: current {curr_val:+.1f}% vs historical {hist_val:+.1f}%")

        if matches > 0:
            similarities.append({
                "crash": crash_name,
                "similarity_pct": round((score / matches) * 100, 1),
                "matching_indicators": matches,
                "details": details[:5],
            })

    similarities.sort(key=lambda item: item["similarity_pct"], reverse=True)
    return similarities


def get_ai_prediction(correlations, relationships, similarities, current_data):
    """Generate an optional model-assisted scenario summary."""
    if not ANTHROPIC_KEY:
        print("⚠️  No ANTHROPIC_API_KEY configured. Skipping model-assisted summary.")
        return None

    import requests as req

    top_corr = dict(list(correlations.items())[:15])
    top_rel = relationships[:10]
    top_similar = similarities[:3] if similarities else []

    live_path = f"{DATA_PATH}/live/latest.json"
    live_data = {}
    if os.path.exists(live_path):
        with open(live_path, encoding="utf-8") as file:
            live_data = json.load(file)

    prompt = f"""You are preparing a macro research scenario summary for Anteroom World Model.

Do not present outputs as financial advice or guaranteed predictions. Treat the data as exploratory research signals.

HISTORICAL CORRELATIONS:
{json.dumps(top_corr, indent=2)}

LEAD-LAG RELATIONSHIPS:
{json.dumps(top_rel, indent=2)}

CURRENT CONDITIONS VS HISTORICAL STRESS PERIODS:
{json.dumps(top_similar, indent=2)}

CURRENT LIVE MARKET DATA:
{json.dumps(live_data, indent=2)}

Return JSON only in this format:
{{
  "current_era_similarity": "which historical period this most resembles",
  "overall_market_outlook": "BULLISH/BEARISH/NEUTRAL/VOLATILE",
  "confidence": 0-100,
  "key_signals": ["signal1", "signal2", "signal3"],
  "warning_signs": ["warning1", "warning2"],
  "positive_signs": ["positive1", "positive2"],
  "predictions": {{
    "4_weeks": {{"direction": "UP/DOWN/SIDEWAYS", "magnitude": "X%", "reasoning": "..."}},
    "3_months": {{"direction": "UP/DOWN/SIDEWAYS", "magnitude": "X%", "reasoning": "..."}},
    "6_months": {{"direction": "UP/DOWN/SIDEWAYS", "magnitude": "X%", "reasoning": "..."}}
  }},
  "crypto_specific": {{"outlook": "...", "key_driver": "..."}},
  "most_important_indicator_to_watch": "...",
  "summary": "2-3 sentence research summary in plain language"
}}"""

    try:
        response = req.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1500,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )

        result = response.json()
        text = result["content"][0]["text"]
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)

    except Exception as exc:
        print(f"❌ Scenario summary error: {exc}")
        return None


def save_analysis(correlations, relationships, crash_patterns, similarities, prediction):
    """Persist the current analysis and update the dashboard snapshot."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    analysis = {
        "generated_at": datetime.now().isoformat(),
        "top_correlations": dict(list(correlations.items())[:20]),
        "lead_lag_relationships": relationships[:20],
        "crash_patterns_found": len(crash_patterns),
        "current_similarity": similarities[:5] if similarities else [],
        "ai_prediction": prediction,
    }

    path = f"{DATA_PATH}/predictions/analysis_{timestamp}.json"
    with open(path, "w", encoding="utf-8") as file:
        json.dump(analysis, file, indent=2)

    latest_path = f"{DATA_PATH}/predictions/latest.json"
    with open(latest_path, "w", encoding="utf-8") as file:
        json.dump(analysis, file, indent=2)

    print(f"✅ Analysis saved: {path}")
    return analysis


if __name__ == "__main__":
    print("=" * 60)
    print("🧠 ANTEROOM WORLD MODEL - ANALYSIS ENGINE")
    print("=" * 60)

    print("\n📂 Loading datasets...")
    data = load_all_data()

    if not data:
        print("❌ No datasets found. Run: python data_collector.py")
        raise SystemExit(1)

    print(f"\n✅ {len(data)} datasets loaded")

    print("\n🔗 Merging time series...")
    df = merge_data(data)
    print(f"   Combined shape: {df.shape}")

    print("\n📊 Calculating correlations...")
    correlations = find_correlations(df)
    print(f"   {len(correlations)} correlations found")

    print("\n⏱️  Detecting lead-lag relationships...")
    relationships = find_lead_lag_relationships(df)
    print(f"   {len(relationships)} relationships found")

    print("\n📜 Extracting historical stress patterns...")
    crash_patterns = extract_crash_patterns(df)
    print(f"   {len(crash_patterns)} stress periods analyzed")

    print("\n🔍 Comparing current conditions to history...")
    similarities = compare_current_to_history(df, crash_patterns)
    if similarities:
        print(f"   Closest match: {similarities[0]['crash']} ({similarities[0]['similarity_pct']}%)")

    print("\n🤖 Generating optional scenario summary...")
    prediction = get_ai_prediction(correlations, relationships, similarities, df)

    if prediction:
        print(f"\n{'=' * 60}")
        print("📋 SCENARIO SUMMARY")
        print(f"   Outlook: {prediction.get('overall_market_outlook')}")
        print(f"   Confidence: {prediction.get('confidence')}%")
        print(f"   Similar to: {prediction.get('current_era_similarity')}")
        print(f"   Summary: {prediction.get('summary')}")
        print(f"{'=' * 60}")

    save_analysis(correlations, relationships, crash_patterns, similarities, prediction)
    print("\n✅ Complete. Launch dashboard with: python dashboard.py")
