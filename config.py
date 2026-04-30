import os

# ============================================================
# ANTEROOM WORLD MODEL - CONFIG
# ============================================================

# Load from environment instead of hardcoding
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Data storage path
DATA_PATH = "./anteroom_data"

# Historical range
HISTORY_FROM_YEAR = 1871

# Live update interval (seconds)
UPDATE_INTERVAL = 300

# Minimum confidence threshold (for summaries)
MIN_CONFIDENCE = 65

# ============================================================
# DATASETS
# ============================================================
DATASETS = {
    "sp500": True,
    "gold": True,
    "oil": True,
    "dollar": True,
    "bitcoin": True,
    "inflation": True,
    "gdp": True,
    "unemployment": True,
    "interest": True,
    "vix": True,
    "nasdaq": True,
    "dxy": True,
    "bonds": True,
    "copper": True,
    "crypto_total": True,
}
