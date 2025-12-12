import os
import csv
import json
from flask import Flask, render_template, request, redirect, url_for, abort
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder

# ==================================================
# PATH DATI
# ==================================================
DATA_DIR = r"C:\Users\U495823\Desktop\results\_dashboard"

FILES = {
    "iv": "iv_surface_all.csv",
    "crash": "crash_probabilities_all.csv",
    "rnd": "rnd_mode_all.csv",
    "mnd": "mnd_mode_all.csv",
    "opt": "option_pricing_all.csv"
}

app = Flask(__name__)

# ==================================================
# UTIL
# ==================================================
def load_csv(name):
    path = os.path.join(DATA_DIR, FILES[name])
    if not os.path.exists(path):
        abort(500, f"File mancante: {path}")
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def fig_json(fig):
    return json.dumps(fig, cls=PlotlyJSONEncoder)

# ==================================================
# LOAD DATA
# ==================================================
IV = load_csv("iv")
CRASH = load_csv("crash")
RND = load_csv("rnd")
MND = load_csv("mnd")
OPT = load_csv("opt")

# ==================================================
# FILTERS
# ==================================================
def unique(seq):
    return sorted(set(x for x in seq if x))

def tickers():
    return unique(r["Ticker"] for r in IV)

def expiries(ticker):
    return unique(r["Expiry"] for r in IV if r["Ticker"] == ticker)

def dates(ticker, expiry):
    return unique(
        r["Data"] for r in IV
        if r["Ticker"] == ticker and r["Expiry"] == expiry
    )

# ==================================================
# ROUTES
# ==================================================
@app.route("/")
def index():
    t = tickers()[0]
    e = expiries(t)[0]
    d = dates(t, e)[0]
    return render_template(
        "index.html",
        title="Dashboard Tesi – IV / RND / MND",
        tickers=tickers(),
        expiries=expiries(t),
        dates=dates(t, e),
        default_ticker=t,
        default_expiry=e,
        default_date=d
    )

@app.route("/ppt")
def ppt():
    t = tickers()[0]
    e = expiries(t)[0]
    d = dates(t, e)[0]
    return redirect(url_for("dashboard", ticker=t, expiry=e, data=d))

@app.route("/dashboard")
def dashboard():
    ticker = request.args["ticker"]
    expiry = request.args["expiry"]
    data = request.args["data"]

    # ---------- IV SMILE ----------
    iv_sel = [
        r for r in IV
        if r["Ticker"] == ticker and r["Expiry"] == expiry and r["Data"] == data
    ]

    fig_smile = go.Figure()
    fig_smile.add_trace(go.Scatter(
        x=[float(r["Moneyness"]) for r in iv_sel],
        y=[float(r["IV"]) for r in iv_sel],
        mode="lines+markers"
    ))
    fig_smile.update_layout(title="IV Smile")

    # ---------- CRASH ----------
    crash_sel = [
        r for r in CRASH
        if r["Ticker"] == ticker and r["Data"] == data
    ]

    fig_crash = go.Figure()
    fig_crash.add_bar(
        x=[r["Modello"] for r in crash_sel],
        y=[float(r["P_crash_Q (RND)"]) for r in crash_sel],
        name="RND"
    )
    fig_crash.add_bar(
        x=[r["Modello"] for r in crash_sel],
        y=[float(r["P_crash_P (MND)"]) for r in crash_sel],
        name="MND"
    )
    fig_crash.update_layout(barmode="group", title="Crash probabilities")

    return render_template(
        "dashboard.html",
        title=f"Dashboard – {ticker}",
        tickers=tickers(),
        expiries=expiries(ticker),
        dates=dates(ticker, expiry),
        ticker=ticker,
        expiry=expiry,
        data=data,
        fig_smile=fig_json(fig_smile),
        fig_crash=fig_json(fig_crash)
    )

if __name__ == "__main__":
    app.run(debug=True)
