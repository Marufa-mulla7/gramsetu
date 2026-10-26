"""Sell/hold advisor: uses the trained models to advise on tomato storage."""
import json
import math
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "tomato_daily.csv"
MODEL_DIR = ROOT / "models"
MIN_NET_GAIN_PCT = 5.0  # only recommend holding if the profit after storage cost is worth it


def make_features(s):
    """Must stay identical to make_features() in scripts/train_model.py."""
    f = pd.DataFrame(index=s.index)
    f["r7"] = np.log(s / s.shift(7))
    f["r14"] = np.log(s / s.shift(14))
    f["r30"] = np.log(s / s.shift(30))
    f["dev30"] = np.log(s / s.rolling(30).mean())
    f["dev90"] = np.log(s / s.rolling(90).mean())
    f["vol30"] = np.log(s).diff().rolling(30).std()
    doy = s.index.day_of_year
    f["season_sin"] = np.sin(2 * np.pi * doy / 365)
    f["season_cos"] = np.cos(2 * np.pi * doy / 365)
    return f


@lru_cache(maxsize=1)
def _load():
    df = pd.read_csv(DATA_FILE, parse_dates=["date"]).set_index("date").asfreq("D")
    df["price"] = df["price"].interpolate()
    s = df["price"].rolling(7, min_periods=1).median()
    info = json.loads((MODEL_DIR / "model_info.json").read_text())
    models = {int(h): joblib.load(MODEL_DIR / f"price_model_{h}d.joblib") for h in info["horizons"]}
    return s, models, info


def get_advice(storage_cost_per_qtl_week: float):
    s, models, info = _load()
    features = make_features(s).iloc[[-1]]
    now = float(s.iloc[-1])

    options = []
    for horizon, model in sorted(models.items()):
        change = float(model.predict(features[info["features"]])[0])  # log change
        sigma = info["horizons"][str(horizon)]["residual_std_log"]
        predicted = now * math.exp(change)
        storage_cost = storage_cost_per_qtl_week * horizon / 7
        net_gain = predicted - now - storage_cost
        options.append(
            {
                "hold_days": horizon,
                "predicted_price": round(predicted),
                "likely_range": [round(now * math.exp(change - sigma)), round(now * math.exp(change + sigma))],
                "storage_cost_per_qtl": round(storage_cost),
                "net_gain_per_qtl": round(net_gain),
                "net_gain_pct": round(net_gain / now * 100, 1),
            }
        )

    best = max(options, key=lambda o: o["net_gain_pct"])
    if best["net_gain_pct"] >= MIN_NET_GAIN_PCT:
        action = "HOLD"
        message = (
            f"Prices may rise to about Rs {best['predicted_price']}/quintal in {best['hold_days']} days. "
            f"After storage cost, you could gain about Rs {best['net_gain_per_qtl']} per quintal."
        )
    else:
        action = "SELL_NOW"
        message = "The expected price rise does not cover storage cost, or prices may fall. Selling now looks safer."

    return {
        "crop": "Tomato",
        "region": "Karnataka (median across markets)",
        "current_price": round(now),
        "price_data_as_of": str(s.index[-1].date()),
        "recommendation": action,
        "best_hold_days": best["hold_days"] if action == "HOLD" else 0,
        "message": message,
        "options": options,
        "model_accuracy": info["horizons"],
        "disclaimer": "Prices are volatile and forecasts can be wrong. This is guidance, not a guarantee.",
    }