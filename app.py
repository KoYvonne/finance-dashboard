"""
Finance Dashboard - Cloud Server
Proxies Yahoo Finance API and serves the dashboard.
"""
import json
import urllib.request
import urllib.parse
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static")


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/yahoo")
def proxy_yahoo():
    symbol = request.args.get("symbol", "")
    range_ = request.args.get("range", "5d")

    if not symbol:
        return jsonify({"error": "Missing symbol"}), 400

    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{urllib.parse.quote(symbol)}"
        f"?range={range_}&interval=1d&includePrePost=false"
    )

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()

        response = app.response_class(
            response=data,
            status=200,
            mimetype="application/json",
        )
        response.headers["Cache-Control"] = "public, max-age=300"
        return response

    except urllib.error.HTTPError as e:
        return jsonify({"error": f"Yahoo Finance: {e.code}"}), e.code
    except Exception as e:
        return jsonify({"error": str(e)}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
