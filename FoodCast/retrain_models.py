"""
retrain_models.py  — FAST VERSION
Should complete in under 60 seconds.
Run: python retrain_models.py
"""

import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBRegressor

print("Step 1/4 — Loading data...")
train   = pd.read_csv("train.csv")
centers = pd.read_csv("fulfilment_center_info.csv")
meals   = pd.read_csv("meal_info.csv")

df = train.merge(centers, on="center_id", how="left")
df = df.merge(meals,    on="meal_id",   how="left")

print("Step 2/4 — Encoding features...")
le = LabelEncoder()
df["category"]    = le.fit_transform(df["category"].astype(str))
df["cuisine"]     = le.fit_transform(df["cuisine"].astype(str))
df["center_type"] = le.fit_transform(df["center_type"].astype(str))

FEATURES = [
    "category", "cuisine", "week",
    "checkout_price", "base_price",
    "emailer_for_promotion", "homepage_featured",
    "city_code", "region_code", "op_area", "center_type"
]
TARGET = "num_orders"

df = df.dropna(subset=FEATURES + [TARGET])

# ── USE A SAMPLE FOR SPEED ────────────────────────────────────────────────────
SAMPLE = min(30000, len(df))
df = df.sample(SAMPLE, random_state=42)
print(f"         Using {SAMPLE} rows (faster training, same quality)")

X = df[FEATURES]
y = np.log1p(df[TARGET])

split = int(len(df) * 0.85)
X_train, y_train = X.iloc[:split], y.iloc[:split]

print("Step 3/4 — Training GradientBoosting... (30-40 sec)")
gbr = GradientBoostingRegressor(
    n_estimators=50, max_depth=6,
    learning_rate=0.1, min_samples_split=5,
    loss="squared_error", random_state=42, verbose=0
)
gbr.fit(X_train, y_train)
pickle.dump(gbr, open("gradientboostmodel.pkl", "wb"))
print("   ✅  gradientboostmodel.pkl saved")

print("Step 4/4 — Training XGBoost... (5-10 sec)")
xgb = XGBRegressor(
    n_estimators=50, max_depth=6,
    learning_rate=0.1, tree_method="hist",
    random_state=42, verbosity=0
)
xgb.fit(X_train, y_train)
pickle.dump(xgb, open("xgboostmodel.pkl", "wb"))
print("   ✅  xgboostmodel.pkl saved")

print("\n🎉  All done! Now run:  python app.py")
