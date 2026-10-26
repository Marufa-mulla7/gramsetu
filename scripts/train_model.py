"""Train models that predict how tomato prices will change over the next 7 and 14 days."""
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HORIZONS = [7, 14]   # days ahead we predict
TEST_DAYS = 180      # most recent ~6 months are kept aside for an honest test

# ---------- 1. Load and smooth the daily prices ----------
df = pd.read_csv("data/tomato_daily.csv", parse_dates=["date"])
df = df.set_index("date").asfreq("D")                          # one row per calendar day
df["price"] = df["price"].interpolate()                        # fill the few missing days
df["smooth"] = df["price"].rolling(7, min_periods=1).median()  # reduce day-to-day noise
s = df["smooth"]


# ---------- 2. Features: what the model gets to see ----------
def make_features(s):
    f = pd.DataFrame(index=s.index)
    f["r7"] = np.log(s / s.shift(7))      # % change over last 7 days
    f["r14"] = np.log(s / s.shift(14))
    f["r30"] = np.log(s / s.shift(30))
    f["dev30"] = np.log(s / s.rolling(30).mean())   # how far above/below the 30-day average
    f["dev90"] = np.log(s / s.rolling(90).mean())
    f["vol30"] = np.log(s).diff().rolling(30).std() # how jumpy prices have been
    doy = s.index.day_of_year
    f["season_sin"] = np.sin(2 * np.pi * doy / 365) # time of year
    f["season_cos"] = np.cos(2 * np.pi * doy / 365)
    return f


X = make_features(s)
feature_cols = list(X.columns)
info = {"features": feature_cols, "horizons": {}}

for H in HORIZONS:
    # Target = log of (future price / today's price), i.e. the % change
    y = np.log(s.shift(-H) / s).rename("y")
    data = pd.concat([X, y, s.rename("now")], axis=1).dropna()
    train, test = data.iloc[:-TEST_DAYS], data.iloc[-TEST_DAYS:]

    model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    model.fit(train[feature_cols], train["y"])

    # ---------- 3. Honest evaluation on unseen recent months ----------
    actual = test["now"] * np.exp(test["y"])
    pred_y = model.predict(test[feature_cols])
    pred = test["now"] * np.exp(pred_y)

    base_mape = np.mean(np.abs(actual - test["now"]) / actual) * 100   # "price stays same"
    model_mape = np.mean(np.abs(actual - pred) / actual) * 100
    model_mae = np.mean(np.abs(actual - pred))
    went_up = test["y"] > 0
    direction = float(((pred_y > 0) == went_up).mean() * 100)
    majority = float(max(went_up.mean(), 1 - went_up.mean()) * 100)    # always guess most common

    print(f"\n=== Predicting {H} days ahead "
          f"(test: {test.index.min().date()} to {test.index.max().date()}) ===")
    print(f"Baseline (price stays same): error {base_mape:5.1f}%")
    print(f"Our model:                   error {model_mape:5.1f}%   (avg miss Rs {model_mae:.0f}/quintal)")
    print(f"Up/down direction correct:   {direction:.0f}%   (guessing the common answer: {majority:.0f}%)")

    # ---------- 4. Retrain on ALL data and save ----------
    model.fit(data[feature_cols], data["y"])
    joblib.dump(model, f"models/price_model_{H}d.joblib")
    info["horizons"][str(H)] = {
        "baseline_error_pct": round(base_mape, 1),
        "model_error_pct": round(model_mape, 1),
        "direction_accuracy_pct": round(direction),
        "majority_guess_pct": round(majority),
        "residual_std_log": round(float(np.std(test["y"] - pred_y)), 3),
        "test_period": [str(test.index.min().date()), str(test.index.max().date())],
    }

with open("models/model_info.json", "w") as f:
    json.dump(info, f, indent=2)
print("\nSaved models/price_model_7d.joblib, price_model_14d.joblib and model_info.json")