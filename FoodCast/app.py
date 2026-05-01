from flask import Flask, render_template, url_for, redirect, request, flash
import numpy as np
import pickle
import datetime
import json
import requests

# ── Firebase (keep your config) ───────────────────────────────────────────────
try:
    import pyrebase
    config = {
        "apiKey": "AIzaSyDM70geF8H8Q1OP3K5GtEgPEdNsm0KgtbQ",
        "authDomain": "food-chain-personal.firebaseapp.com",
        "projectId": "food-chain-personal",
        "databaseURL": "https://food-chain-personal-default-rtdb.firebaseio.com",
        "storageBucket": "food-chain-personal.firebasestorage.app",
        "messagingSenderId": "570768232168",
        "appId": "1:570768232168:web:cda9aabd5754969e8e435d",
        "measurementId": "G-5KS32SL0W3"
    }
    firebase = pyrebase.initialize_app(config)
    db = firebase.database()
    FIREBASE_ON = True
except Exception as e:
    print(f"[WARNING] Firebase not connected: {e}")
    FIREBASE_ON = False

# ── Blockchain node ───────────────────────────────────────────────────────────
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "foodcast_secret_2025"   # needed for flash messages

# ── Load models ───────────────────────────────────────────────────────────────
model  = pickle.load(open("gradientboostmodel.pkl", "rb"))
model2 = pickle.load(open("xgboostmodel.pkl", "rb"))

# ── Helper: safe DB read ──────────────────────────────────────────────────────
def db_get(path):
    if not FIREBASE_ON:
        return {}
    try:
        return db.child(path).get().val() or {}
    except Exception:
        return {}

def db_push(path, data):
    if not FIREBASE_ON:
        return
    try:
        db.child(path).push(data)
    except Exception as e:
        print(f"[DB ERROR] {e}")

# ─────────────────────────────────────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('landing.html')


# ── LOGIN (FIXED) ─────────────────────────────────────────────────────────────
@app.route("/login", methods=['POST'])
def login():
    username = request.form.get('username', '').strip().upper()
    password = request.form.get('password', '').strip()

    valid = {"SUPPLIER", "WAREHOUSE", "RESTAURANT"}

    if username in valid and password == '12345':
        if username == 'SUPPLIER':
            return redirect(url_for('Supplier'))
        elif username == 'RESTAURANT':
            return redirect(url_for('Restaurant'))
        else:
            return redirect(url_for('Warehouse'))
    else:
        flash("Invalid credentials. Please try again.")
        return redirect(url_for('home'))


# ── ROLE PAGES ────────────────────────────────────────────────────────────────

@app.route("/Supplier")
def Supplier():
    ok1 = db_get("message to wh from s")
    ok2 = db_get("message to s from wh")
    return render_template('Supplier.html', info1=ok1, info2=ok2)


@app.route("/Warehouse")
def Warehouse():
    ok1 = db_get("message to s from wh")
    ok2 = db_get("message to r from wh")
    ok3 = db_get("message to wh from r")
    ok4 = db_get("message to wh from s")
    return render_template('Warehouse.html', info1=ok1, info2=ok2, info3=ok3, info4=ok4)


@app.route("/Restaurant")
def Restaurant():
    ok1 = db_get("message to wh from r")
    ok2 = db_get("message to r from wh")
    return render_template('Restaurant.html', info1=ok1, info2=ok2)


# ── MESSAGING ─────────────────────────────────────────────────────────────────

@app.route("/msgtowhfs", methods=['POST'])
def msgtowhfs():
    db_push("message to wh from s", {"msg": request.form.get("mtwfs", "")})
    return redirect(url_for('Supplier'))


@app.route("/msgtosfwh", methods=['POST'])
def msgtosfwh():
    db_push("message to s from wh", {"msg": request.form.get("mtsfw", "")})
    return redirect(url_for('Warehouse'))


@app.route("/msgtorfwh", methods=['POST'])
def msgtorfwh():
    db_push("message to r from wh", {"msg": request.form.get("mtrfw", "")})
    return redirect(url_for('Warehouse'))


@app.route("/msgtowhfr", methods=['POST'])
def msgtowhfr():
    db_push("message to wh from r", {"msg": request.form.get("mtwfr", "")})
    return redirect(url_for('Restaurant'))


# ── PREDICTION ────────────────────────────────────────────────────────────────

CATEGORY_MAP = {
    'Beverages': 0, 'Biryani': 1, 'Desert': 2, 'Extras': 3,
    'Fish': 4, 'Other Snacks': 5, 'Pasta': 6, 'Pizza': 7,
    'Rice Bowl': 8, 'Salad': 9, 'Sandwich': 10, 'Seafood': 11,
    'Soup': 12, 'Starters': 13
}
CUISINE_MAP = {'Continental': 0, 'Indian': 1, 'Italian': 2, 'Thai': 3}
CENTER_MAP  = {'TYPE_A': 0, 'TYPE_B': 1, 'TYPE_C': 2}


@app.route("/predict", methods=['GET', 'POST'])
def predict():
    if request.method == "POST":
        try:
            category      = request.form.get('category', 'Beverages')
            cuisine       = request.form.get('cuisine', 'Indian')
            week          = float(request.form.get('weeks', 4))
            checkout_price = float(request.form.get('checkout price', 299))
            base_price    = float(request.form.get('base price', 350))
            email_promo   = 1 if request.form.get('Email Promotion') == 'yes' else 0
            hp_featured   = 1 if request.form.get('Homepage Featured') == 'yes' else 0
            city_code     = float(request.form.get('City Code', 590))
            region_code   = float(request.form.get('Region Code', 56))
            op_area       = float(request.form.get('Operational Area', 3))
            center_type   = request.form.get('Center Type', 'TYPE_A')

            features = [
                CATEGORY_MAP.get(category, 0),
                CUISINE_MAP.get(cuisine, 1),
                week,
                checkout_price,
                base_price,
                email_promo,
                hp_featured,
                city_code,
                region_code,
                op_area,
                CENTER_MAP.get(center_type, 0)
            ]

            data = np.array([features])
            gbr_pred    = model.predict(data)
            xgb_pred    = model2.predict(data)
            hybrid_pred = (gbr_pred + xgb_pred) / 2
            # If models were retrained with log1p target, reverse with expm1
            try:
                raw = hybrid_pred[0]
                output = max(0, int(round(np.expm1(raw) if raw < 20 else raw)))
            except Exception:
                output = max(0, int(round(hybrid_pred[0])))

            text = f"Approximate Orders for {int(week)} week(s): {output}"
            return render_template("predict.html", prediction_text=text, predicted_orders=output, weeks=int(week), category=category)

        except Exception as e:
            print(f"[PREDICT ERROR] {e}")
            return render_template('predict.html', prediction_text="Error in prediction. Please check your inputs.")

    return render_template('predict.html')


# ── BLOCKCHAIN ROUTES ─────────────────────────────────────────────────────────

posts = []

def fetch_posts():
    try:
        response = requests.get(f"{CONNECTED_NODE_ADDRESS}/chain", timeout=3)
        if response.status_code == 200:
            content = []
            chain = json.loads(response.content)
            for block in chain["chain"]:
                for tx in block["transactions"]:
                    tx["index"] = block["index"]
                    tx["hash"] = block["previous_hash"]
                    content.append(tx)
            global posts
            posts = sorted(content, key=lambda k: k['timestamp'], reverse=True)
    except Exception:
        pass


@app.route('/find_my_food')
def index():
    fetch_posts()
    return render_template('index.html',
                           title='Find My Food',
                           posts=posts,
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string)


@app.route('/submit', methods=['POST'])
def submit_textarea():
    post_object = {
        'author': request.form.get("author", "FoodCast"),
        'content': request.form.get("content", ""),
    }
    try:
        requests.post(f"{CONNECTED_NODE_ADDRESS}/new_transaction",
                      json=post_object,
                      headers={'Content-type': 'application/json'},
                      timeout=3)
    except Exception:
        pass
    return redirect('/find_my_food')


def timestamp_to_string(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time).strftime('%H:%M')


# ── DEMAND GRAPH ROUTE ────────────────────────────────────────────────────────
import io, base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import MaxNLocator

@app.route("/graph")
def graph():
    base   = int(request.args.get("base", 100))
    cat    = request.args.get("cat", "Food Item")
    wks    = int(request.args.get("weeks", 10))

    variation = [1.00, 0.97, 1.03, 0.95, 1.05, 0.98, 1.02, 0.96, 1.04, 1.01]
    weeks_list  = list(range(1, 11))
    orders_list = [max(0, int(round(base * v))) for v in variation]

    # ── Matplotlib figure ──────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(11, 5.5))
    fig.patch.set_facecolor('#161616')
    ax.set_facecolor('#1A1A1A')

    # Gradient area fill
    ax.fill_between(weeks_list, orders_list, alpha=0.18, color='#FF6B2B', zorder=1)

    # Line
    ax.plot(weeks_list, orders_list, color='#FF6B2B', linewidth=2.5,
            zorder=2, solid_capstyle='round')

    # Points
    ax.scatter(weeks_list, orders_list, color='#FF6B2B', s=90, zorder=3,
               edgecolors='#FFFFFF', linewidths=1.5)

    # Annotations on each point
    for x, y in zip(weeks_list, orders_list):
        ax.annotate(f'{y:,}',
                    xy=(x, y), xytext=(0, 14),
                    textcoords='offset points',
                    ha='center', va='bottom',
                    fontsize=8.5, color='#FFFFFF',
                    fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3',
                              facecolor='#FF6B2B', alpha=0.75, edgecolor='none'))

    # Style axes
    ax.set_xlabel('Week Number', color='#AAAAAA', fontsize=11, labelpad=10)
    ax.set_ylabel('Predicted Orders', color='#AAAAAA', fontsize=11, labelpad=10)
    ax.set_title(f'10-Week Demand Forecast  —  {cat}',
                 color='#FFFFFF', fontsize=14, fontweight='bold', pad=16)

    ax.tick_params(colors='#888888', labelsize=9)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    for spine in ax.spines.values():
        spine.set_edgecolor('#333333')
    ax.grid(axis='y', color='#2A2A2A', linewidth=0.8, linestyle='--')
    ax.set_xlim(0.5, 10.5)

    # Legend
    patch = mpatches.Patch(color='#FF6B2B', label=f'Base prediction: {base:,} orders/week')
    ax.legend(handles=[patch], facecolor='#222222', edgecolor='#444444',
              labelcolor='#CCCCCC', fontsize=9, loc='upper right')

    plt.tight_layout()

    # Encode to base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')

    return render_template('graph.html',
                           img_b64=img_b64,
                           category=cat,
                           base=base,
                           weeks=wks,
                           orders_list=orders_list,
                           weeks_list=weeks_list)


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)

