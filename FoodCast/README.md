# FoodCast — Food Demand Forecasting & Inventory Management
## Final Year Project | IEEE Access DOI: 10.1109/ACCESS.2023.3266275

---

## What Was Changed (vs Original Project)

### 1. UI/Design — Complete Redesign
- Dark premium theme (#0F0F0F background) inspired by award-winning food/drink sites
- Animated particle system, glowing radial backgrounds, scroll-reveal animations
- Playfair Display serif font for headings — premium editorial feel
- All pages: Landing, Predict, Supplier, Warehouse, Restaurant redesigned

### 2. Login Bug — FIXED
- Original bug: form submitted `username` as the role but `login()` compared
  against a fixed string — broke when dropdown value had extra whitespace or
  casing difference
- Fix: `.strip().upper()` on both username and password inputs
- Flash messages now display on wrong credentials instead of silent redirect

### 3. Predict Page — Enhanced
- Count-up animation on predicted number
- Auto-generates Next 10-Week Forecast table from single prediction
- IEEE accuracy metrics panel (RMSE, MAPE, MAE, RMSLE) always visible
- Loading state on Predict button

### 4. Role Dashboards — Redesigned
- Unified `base_role.html` template — all 3 roles extend it
- Cards with icons for each message section
- Restaurant dashboard has a quick shortcut to the Predict page
- Firebase errors are caught gracefully — app works even if Firebase is offline

### 5. app.py — Improvements
- All category/cuisine/center encodings moved to dictionaries (clean)
- Firebase wrapped in try/except — won't crash if offline
- Blockchain requests use timeout=3 — won't hang
- Better input validation in /predict with try/except

### 6. Algorithm Used (IEEE Paper Validated)
- **Gradient Boosting Regressor**: 100 trees, depth 9, lr 0.1, squared error loss
- **XGBoost Regressor**: 100 trees, depth 9, lr 0.1, exact tree method
- **Hybrid Ensemble**: (GBR + XGB) / 2 — reduces variance
- **Blockchain**: SHA-256 Proof-of-Work, difficulty=2, immutable transaction log

---

## Step-by-Step Setup & Run Commands

### Step 1 — Install Python Dependencies
```bash
pip install flask pyrebase4 numpy scikit-learn xgboost requests
```

### Step 2 — Go into the project folder
```bash
cd updated_project
```

### Step 3 — Terminal 1: Run the Flask app
```bash
python app.py
```
Open browser: http://127.0.0.1:5000

### Step 4 — Terminal 2: Run the Blockchain node (optional)
```bash
python block_chain.py
```
This runs at http://127.0.0.1:8000

---

## Login Credentials
| Role       | Username  | Password |
|------------|-----------|----------|
| Supplier   | SUPPLIER  | 12345    |
| Warehouse  | WAREHOUSE | 12345    |
| Restaurant | RESTAURANT| 12345    |

---

## Project Structure
```
updated_project/
├── app.py                    ← Main Flask app (login fixed)
├── block_chain.py            ← Blockchain node (run separately)
├── gradientboostmodel.pkl    ← Trained GBR model
├── xgboostmodel.pkl          ← Trained XGBoost model
├── train.csv / test.csv      ← Dataset
├── meal_info.csv             ← Meal metadata
├── fulfilment_center_info.csv← Centre metadata
├── templates/
│   ├── landing.html          ← Home + Login page (redesigned)
│   ├── predict.html          ← Demand prediction page (redesigned)
│   ├── base_role.html        ← Shared layout for role dashboards
│   ├── Supplier.html         ← Supplier dashboard
│   ├── Warehouse.html        ← Warehouse dashboard
│   └── Restaurant.html       ← Restaurant dashboard
└── static/
    └── main.css              ← Original CSS (kept)
```

---

## Future Scope
1. Add LSTM model — IEEE paper shows 6.56% MAPE vs ~10% for tree models
2. Add LightGBM and CatBoost (best ML model in the paper — RMSLE 0.29)
3. Add lag features (past 10 weeks of orders) for better time-series accuracy
4. EWMA features — exponentially weighted moving average (alpha=0.5)
5. Export forecast as CSV/Excel for restaurant managers
6. Firebase Authentication instead of hardcoded passwords
7. SHAP explainability — show which feature influenced each prediction
8. Mobile app (Flutter) for Supplier and Restaurant roles
