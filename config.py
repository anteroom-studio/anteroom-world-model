import os
from pathlib import Path

# ============================================================
# ANTEROOM WORLD MODEL - CONFIGURATION
# ============================================================


def load_local_env(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_local_env()

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DATA_PATH = os.getenv("ANTEROOM_DATA_PATH", "./anteroom_data")
HISTORY_FROM_YEAR = int(os.getenv("ANTEROOM_HISTORY_FROM_YEAR", "1871"))
UPDATE_INTERVAL = int(os.getenv("ANTEROOM_UPDATE_INTERVAL", "300"))
MIN_CONFIDENCE = int(os.getenv("ANTEROOM_MIN_CONFIDENCE", "65"))

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
