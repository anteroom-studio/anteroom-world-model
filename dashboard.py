"""
ZAI World Model - Live Dashboard
Terminal mein sab kuch dikhata hai - 24/7 running
"""

import os
import json
import time
import subprocess
from datetime import datetime
from config import DATA_PATH, UPDATE_INTERVAL, ANTHROPIC_KEY

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def load_latest():
    try:
        with open(f"{DATA_PATH}/predictions/latest.json") as f:
            return json.load(f)
    except:
        return None

def load_live():
    try:
        with open(f"{DATA_PATH}/live/latest.json") as f:
            return json.load(f)
    except:
        return None

def arrow(val):
    if val is None:
        return "~"
    return "↑" if float(val) > 0 else "↓"

def color_val(val):
    """Simple +/- indicator"""
    if val is None:
        return "N/A"
    v = float(val)
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.2f}%"

def display(tick=0):
    clear()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("╔══════════════════════════════════════════════════════════╗")
    print("║          ZAI WORLD MODEL - MARKET PREDICTION AI          ║")
    print(f"║                    {now}                  ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    # Live market data
    live = load_live()
    if live:
        print("\n📊 LIVE MARKETS:")
        print("─" * 60)
        
        items = [
            ("S&P 500",   live.get("sp500")),
            ("NASDAQ",    live.get("nasdaq")),
            ("Gold",      live.get("gold")),
            ("Oil (WTI)", live.get("oil")),
            ("USD Index", live.get("dollar")),
            ("VIX Fear",  live.get("vix")),
            ("Bitcoin",   live.get("bitcoin")),
            ("Ethereum",  live.get("ethereum")),
        ]
        
        for name, d in items:
            if d:
                price = d.get("price", 0)
                chg = d.get("change_pct", 0)
                arr = "↑" if chg > 0 else "↓"
                sign = "+" if chg > 0 else ""
                print(f"  {name:<12} ${price:>12,.2f}   {arr} {sign}{chg:.2f}%")
    else:
        print("\n⚠️  Live data nahi mili. data_collector.py chalao.")
    
    # AI Prediction
    analysis = load_latest()
    if analysis and analysis.get("ai_prediction"):
        pred = analysis["ai_prediction"]
        
        print("\n🤖 ZAI AI PREDICTION:")
        print("─" * 60)
        
        outlook = pred.get("overall_market_outlook", "N/A")
        era = pred.get("current_era_similarity", "N/A")

        # the model fills confidence as "0-100" so it can come back as a float
        # (72.5) or out of range. '█' * (conf//10) blows up on a float and the
        # whole display() then dies into the 30s error loop, so clamp to 0-100 int.
        try:
            conf = int(float(pred.get("confidence", 0)))
        except (TypeError, ValueError):
            conf = 0
        conf = max(0, min(100, conf))

        outlook_icon = {"BULLISH": "🟢", "BEARISH": "🔴",
                        "NEUTRAL": "🟡", "VOLATILE": "🟠"}.get(outlook, "⚪")

        print(f"  Outlook:     {outlook_icon} {outlook}")
        print(f"  Confidence:  {'█' * (conf//10)}{'░' * (10-conf//10)} {conf}%")
        print(f"  Similar to:  {era}")
        
        # Predictions
        predictions = pred.get("predictions", {})
        if predictions:
            print("\n  📅 TIMELINE PREDICTIONS:")
            for period, p in predictions.items():
                d = p.get("direction", "?")
                m = p.get("magnitude", "?")
                icon = "↑" if d == "UP" else "↓" if d == "DOWN" else "→"
                print(f"    {period:<12} {icon} {d} ~{m}")
        
        # Crypto
        crypto = pred.get("crypto_specific", {})
        if crypto:
            print(f"\n  🪙 CRYPTO: {crypto.get('outlook', 'N/A')}")
            print(f"     Driver: {crypto.get('key_driver', 'N/A')}")
        
        # Key signals
        signals = pred.get("key_signals", [])
        if signals:
            print("\n  ⚡ KEY SIGNALS:")
            for s in signals[:3]:
                print(f"    • {s}")
        
        # Warnings
        warnings = pred.get("warning_signs", [])
        if warnings:
            print("\n  ⚠️  WARNINGS:")
            for w in warnings[:2]:
                print(f"    • {w}")
        
        # Summary
        summary = pred.get("summary", "")
        if summary:
            print(f"\n  💬 SUMMARY:")
            # Word wrap at 55 chars
            words = summary.split()
            line = "    "
            for word in words:
                if len(line) + len(word) > 58:
                    print(line)
                    line = "    " + word + " "
                else:
                    line += word + " "
            if line.strip():
                print(line)
        
        # Watch indicator
        watch = pred.get("most_important_indicator_to_watch", "")
        if watch:
            print(f"\n  👁️  WATCH: {watch}")
        
        # Similarity to crashes
        sims = analysis.get("current_similarity", [])
        if sims:
            print("\n  📜 HISTORICAL SIMILARITY:")
            for s in sims[:3]:
                bar = "█" * int(s["similarity_pct"] / 10)
                print(f"    {s['crash'][:30]:<30} {bar} {s['similarity_pct']}%")
        
        gen_time = analysis.get("generated_at", "")
        if gen_time:
            print(f"\n  🕐 Analysis generated: {gen_time[:19]}")
    
    else:
        print("\n⚠️  Prediction nahi mili.")
        print("   Chalao: python correlation_engine.py")
    
    print("\n" + "─" * 60)
    print(f"  🔄 Next refresh in {UPDATE_INTERVAL}s  |  Ctrl+C = exit")
    print("─" * 60)

def run_update_cycle():
    """Background mein data update + re-analyze karo"""
    from data_collector import update_live_data
    from correlation_engine import (load_all_data, merge_data, find_correlations,
                                     find_lead_lag_relationships, extract_crash_patterns,
                                     compare_current_to_history, get_ai_prediction, save_analysis)
    
    print("\n🔄 Full analysis update ho rahi hai...")
    
    # Live data update
    update_live_data()
    
    # Re-analyze (every 6 hours)
    data = load_all_data()
    if data:
        df = merge_data(data)
        correlations = find_correlations(df)
        relationships = find_lead_lag_relationships(df)
        crash_patterns = extract_crash_patterns(df)
        similarities = compare_current_to_history(df, crash_patterns)
        prediction = get_ai_prediction(correlations, relationships, similarities, df)
        if prediction:
            save_analysis(correlations, relationships, crash_patterns, similarities, prediction)

# ============================================================
# MAIN LOOP
# ============================================================
if __name__ == "__main__":
    print("🚀 ZAI Dashboard starting...")
    
    if not ANTHROPIC_KEY:
        print("❌ ANTHROPIC_API_KEY not set — add it to .env or your environment")
        exit()
    
    # Check data exists
    if not os.path.exists(f"{DATA_PATH}/historical"):
        print("❌ Data nahi mila! Pehle chalao:")
        print("   python data_collector.py")
        exit()
    
    tick = 0
    last_analysis = 0
    ANALYSIS_INTERVAL = 21600  # 6 hours mein re-analyze
    
    while True:
        try:
            display(tick)
            time.sleep(UPDATE_INTERVAL)
            tick += 1
            
            # Live data update har tick
            from data_collector import update_live_data
            update_live_data()
            
            # Full re-analysis har 6 ghante
            if time.time() - last_analysis > ANALYSIS_INTERVAL:
                run_update_cycle()
                last_analysis = time.time()
                
        except KeyboardInterrupt:
            print("\n\n👋 ZAI Dashboard band. Khuda Hafiz!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(30)
