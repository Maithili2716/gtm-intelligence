from flask import Flask, jsonify, render_template

from app.intelligence.risk import investigate_risk
from app.intelligence.account import analyze_account


app = Flask(
    __name__,
    template_folder="templates",
)


@app.route("/")
def index():
    return render_template(
        "account.html"
    )


@app.route("/api/account/<account_id>")
async def account(account_id):

    # -----------------------------------------
    # LIVE INTELLIGENCE PIPELINE
    # -----------------------------------------

    risk = await investigate_risk(
        account_id
    )

    analysis = await analyze_account(
        account_id=account_id,
        risk=risk,
    )

    # -----------------------------------------
    # RETURN BOTH THE EXECUTIVE SNAPSHOT
    # AND THE REASONING DATA
    # -----------------------------------------

    return jsonify(
        {
            "account": analysis,
            "investigation": risk,
        }
    )


@app.route("/api/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "gtm-intelligence",
        }
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
    )
