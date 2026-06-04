"""
ZAI World Model - Data Collector
Historical data 1800s se aaj tak download karta hai
Phir automatically live update karta rehta hai
"""

import os
import time
import json
import requests
import pandas as pd
from datetime import datetime
from config import DATA_PATH, DATASETS, HISTORY_FROM_YEAR, UPDATE_INTERVAL

# ============================================================
# SETUP
# ============================================================
def setup_folders():
    folders = [
        DATA_PATH,
        f"{DATA_PATH}/historical",
        f"{DATA_PATH}/live",
        f"{DATA_PATH}/patterns",
        f"{DATA_PATH}/predictions",
        f"{DATA_PATH}/logs",
    ]
    for f in folders:
        os.makedirs(f, exist_ok=True)
    print(f"✅ Folders ready: {DATA_PATH}")

# ============================================================
# FREE DATA SOURCES
# ============================================================

def download_fred_data(series_id, name, start_year=None):
    """
    FRED (Federal Reserve) - Free, no API key needed for basic
    Covers: GDP, Inflation, Unemployment, Interest rates, etc.
    """
    # FRED simple URL - no vintage_date parameter
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    
    try:
        print(f"  📥 Downloading {name} from FRED...")
        # Read without parse_dates first
        df = pd.read_csv(url)
        
        # Find date column (could be DATE or first column)
        date_col = None
        for col in df.columns:
            if "date" in col.lower() or col == df.columns[0]:
                date_col = col
                break
        
        if date_col is None:
            raise Exception("No date column found")
        
        # Rename columns
        df = df.rename(columns={date_col: "date", df.columns[-1]: "value"})
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        
        # Filter by start year
        if start_year:
            df = df[df["date"].dt.year >= start_year]
        
        # Remove non-numeric values
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
        df["source"] = "FRED"
        df["series"] = name
        
        path = f"{DATA_PATH}/historical/{name}.csv"
        df.to_csv(path, index=False)
        print(f"  ✅ {name}: {len(df)} records ({df['date'].min().year} - {df['date'].max().year})")
        return df
    except Exception as e:
        print(f"  ❌ {name} error: {e}")
        return None

def download_yahoo_data(ticker, name, start_year=None):
    """
    Yahoo Finance via yfinance library - more reliable
    """
    try:
        import yfinance as yf
    except ImportError:
        import subprocess, sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "--break-system-packages", "-q"])
        import yfinance as yf

    safe_year = max(start_year or 1970, 1970)
    start_str = f"{safe_year}-01-01"

    try:
        print(f"  📥 Downloading {name} ({ticker}) from Yahoo...")
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(start=start_str, interval="1d", auto_adjust=True)

        if df.empty:
            print(f"  ❌ {name}: no data returned")
            return None

        df = df.reset_index()
        df = df.rename(columns={"Date": "date", "Close": "value"})
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
        df = df[["date", "value"]].dropna()
        df["source"] = "Yahoo"
        df["series"] = name

        path = f"{DATA_PATH}/historical/{name}.csv"
        df.to_csv(path, index=False)
        print(f"  ✅ {name}: {len(df)} records ({df['date'].min().year} - {df['date'].max().year})")
        return df
    except Exception as e:
        print(f"  ❌ {name} error: {e}")
        return None

def download_coingecko_data(coin_id, name):
    """
    CoinGecko - Free crypto data with proper headers
    """
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": "max",
    }

    try:
        print(f"  📥 Downloading {name} from CoinGecko...")
        r = requests.get(url, params=params, headers=headers, timeout=60)
        
        if r.status_code == 429:
            print(f"  ⏳ Rate limited, waiting 60s...")
            time.sleep(60)
            r = requests.get(url, params=params, headers=headers, timeout=60)
        
        data = r.json()
        prices = data.get("prices", [])

        if not prices:
            print(f"  ❌ {name}: empty response - {data.get('status', {}).get('error_message', 'unknown')}")
            return None

        df = pd.DataFrame(prices, columns=["timestamp", "value"])
        df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df[["date", "value"]].dropna()
        df["source"] = "CoinGecko"
        df["series"] = name

        path = f"{DATA_PATH}/historical/{name}.csv"
        df.to_csv(path, index=False)
        print(f"  ✅ {name}: {len(df)} records ({df['date'].min().year} - {df['date'].max().year})")
        return df
    except Exception as e:
        print(f"  ❌ {name} error: {e}")
        return None

def download_world_bank_data(indicator, country, name):
    """
    World Bank - Free global economic data going back to 1960
    """
    url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
    params = {
        "format": "json",
        "per_page": 10000,
        "mrv": 100
    }
    
    try:
        print(f"  📥 Downloading {name} from World Bank...")
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        
        if len(data) < 2:
            return None
            
        records = data[1]
        rows = []
        for rec in records:
            if rec.get("value") is not None:
                rows.append({
                    "date": pd.to_datetime(f"{rec['date']}-01-01"),
                    "value": float(rec["value"]),
                    "source": "WorldBank",
                    "series": name
                })
        
        df = pd.DataFrame(rows).sort_values("date")
        path = f"{DATA_PATH}/historical/{name}.csv"
        df.to_csv(path, index=False)
        print(f"  ✅ {name}: {len(df)} records ({df['date'].min().year} - {df['date'].max().year})")
        return df
    except Exception as e:
        print(f"  ❌ {name} error: {e}")
        return None

# ============================================================
# DOWNLOAD ALL HISTORICAL DATA
# ============================================================
def download_all_historical():
    print("\n" + "="*60)
    print("📚 HISTORICAL DATA DOWNLOAD SHURU")
    print("="*60)
    print(f"Storage: {DATA_PATH}")
    print(f"From: {HISTORY_FROM_YEAR}")
    print()

    results = {}

    # --- FRED DATA (Federal Reserve - Most reliable) ---
    print("🏦 FRED (Federal Reserve Data):")
    
    if DATASETS.get("inflation"):
        # CPI - Consumer Price Index (1871 se!)
        results["inflation"] = download_fred_data("CPIAUCNS", "inflation", 1871)
        time.sleep(1)
    
    if DATASETS.get("interest"):
        # Federal Funds Rate
        results["interest"] = download_fred_data("FEDFUNDS", "interest_rate", 1954)
        time.sleep(1)
    
    if DATASETS.get("unemployment"):
        results["unemployment"] = download_fred_data("UNRATE", "unemployment", 1948)
        time.sleep(1)
    
    if DATASETS.get("gdp"):
        results["gdp"] = download_fred_data("GDP", "gdp_usa", 1947)
        time.sleep(1)
    
    if DATASETS.get("bonds"):
        # 10-Year Treasury Yield
        results["bonds"] = download_fred_data("GS10", "treasury_10y", 1962)
        time.sleep(1)
    
    # Money supply M2
    results["m2"] = download_fred_data("M2SL", "money_supply_m2", 1959)
    time.sleep(1)
    
    # Consumer sentiment
    results["sentiment"] = download_fred_data("UMCSENT", "consumer_sentiment", 1952)
    time.sleep(1)

    # --- YAHOO FINANCE ---
    print("\n📈 Yahoo Finance:")
    
    if DATASETS.get("sp500"):
        results["sp500"] = download_yahoo_data("^GSPC", "sp500", 1928)
        time.sleep(2)
    
    if DATASETS.get("nasdaq"):
        results["nasdaq"] = download_yahoo_data("^IXIC", "nasdaq", 1971)
        time.sleep(2)
    
    if DATASETS.get("gold"):
        results["gold"] = download_yahoo_data("GC=F", "gold", 1970)
        time.sleep(2)
    
    if DATASETS.get("oil"):
        results["oil"] = download_yahoo_data("CL=F", "oil_crude", 1983)
        time.sleep(2)
    
    if DATASETS.get("dollar"):
        results["dollar"] = download_yahoo_data("DX-Y.NYB", "dollar_index", 1971)
        time.sleep(2)
    
    if DATASETS.get("vix"):
        results["vix"] = download_yahoo_data("^VIX", "vix_fear", 1990)
        time.sleep(2)
    
    if DATASETS.get("copper"):
        results["copper"] = download_yahoo_data("HG=F", "copper", 1988)
        time.sleep(2)

    # --- COINGECKO ---
    print("\n🪙 CoinGecko (Crypto):")
    
    if DATASETS.get("bitcoin"):
        results["bitcoin"] = download_coingecko_data("bitcoin", "bitcoin")
        time.sleep(3)
    
    results["ethereum"] = download_coingecko_data("ethereum", "ethereum")
    time.sleep(3)
    
    # --- WORLD BANK ---
    print("\n🌍 World Bank (Global):")
    results["world_gdp"] = download_world_bank_data("NY.GDP.MKTP.CD", "WLD", "world_gdp")
    time.sleep(2)
    results["china_gdp"] = download_world_bank_data("NY.GDP.MKTP.CD", "CHN", "china_gdp")
    time.sleep(2)

    # Summary
    success = sum(1 for v in results.values() if v is not None)
    total = len(results)
    
    print(f"\n{'='*60}")
    print(f"✅ Download complete: {success}/{total} datasets")
    print(f"📁 Saved to: {DATA_PATH}/historical/")
    print(f"{'='*60}")
    
    # Save download log
    log = {
        "downloaded_at": datetime.now().isoformat(),
        "datasets": {k: (v is not None) for k, v in results.items()}
    }
    with open(f"{DATA_PATH}/logs/download_log.json", "w") as f:
        json.dump(log, f, indent=2)
    
    return results

# ============================================================
# LIVE DATA UPDATE
# ============================================================
def update_live_data():
    """Har UPDATE_INTERVAL seconds mein latest data fetch karo"""
    print(f"\n🔄 Live data update: {datetime.now().strftime('%H:%M:%S')}")
    
    live_data = {}

    # Latest prices
    tickers = {
        "sp500": "^GSPC",
        "nasdaq": "^IXIC",
        "gold": "GC=F",
        "oil": "CL=F",
        "dollar": "DX-Y.NYB",
        "vix": "^VIX",
    }

    # Yahoo killed the old v7/finance/download CSV endpoint, it now 401s on the
    # crumb/cookie check so the urllib path was silently failing every ticker.
    # Go through yfinance like download_yahoo_data does, it handles the auth.
    try:
        import yfinance as yf
    except ImportError:
        yf = None

    for name, ticker in tickers.items():
        if yf is None:
            break
        try:
            df = yf.Ticker(ticker).history(period="5d", interval="1d", auto_adjust=True)
            if df.empty:
                continue
            closes = df["Close"].dropna()
            latest = float(closes.iloc[-1])
            prev = float(closes.iloc[-2]) if len(closes) > 1 else latest
            change_pct = ((latest - prev) / prev) * 100 if prev else 0.0
            live_data[name] = {
                "price": latest,
                "change_pct": round(change_pct, 2),
                "updated": datetime.now().isoformat()
            }
        except Exception:
            pass
    
    # Bitcoin live
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin,ethereum", "vs_currencies": "usd", "include_24hr_change": "true"},
            timeout=10
        )
        data = r.json()
        live_data["bitcoin"] = {
            "price": data["bitcoin"]["usd"],
            "change_pct": round(data["bitcoin"].get("usd_24h_change", 0), 2),
            "updated": datetime.now().isoformat()
        }
        live_data["ethereum"] = {
            "price": data["ethereum"]["usd"],
            "change_pct": round(data["ethereum"].get("usd_24h_change", 0), 2),
            "updated": datetime.now().isoformat()
        }
    except:
        pass
    
    # Save live data
    path = f"{DATA_PATH}/live/latest.json"
    with open(path, "w") as f:
        json.dump(live_data, f, indent=2)
    
    return live_data

# ============================================================
# CHECK IF DATA EXISTS
# ============================================================
def check_existing_data():
    """Dekho kaunsa data already downloaded hai"""
    historical_path = f"{DATA_PATH}/historical"
    if not os.path.exists(historical_path):
        return []
    files = [f.replace(".csv", "") for f in os.listdir(historical_path) if f.endswith(".csv")]
    return files

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    setup_folders()
    
    existing = check_existing_data()
    
    if existing:
        print(f"\n📂 Existing data found: {', '.join(existing)}")
        ans = input("Re-download karna hai? (y/n): ").strip().lower()
        if ans == "y":
            download_all_historical()
    else:
        print("\n🆕 Pehli baar chal raha hai - sab data download hoga...")
        download_all_historical()
    
    print("\n🔄 Live updates shuru kar raha hun...")
    print("   Ctrl+C se band karo\n")
    
    while True:
        try:
            live = update_live_data()
            for name, d in live.items():
                arrow = "↑" if d["change_pct"] > 0 else "↓"
                print(f"  {name:12} ${d['price']:>12,.2f}  {arrow} {abs(d['change_pct']):.2f}%")
            print(f"  Next update in {UPDATE_INTERVAL}s...")
            time.sleep(UPDATE_INTERVAL)
        except KeyboardInterrupt:
            print("\n👋 Live updates band!")
            break
