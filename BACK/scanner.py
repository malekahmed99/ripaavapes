from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
from flask import abort

app = Flask(__name__)
CSV_FILE = "serials.csv"
TEMPLATE_FILE = os.path.join(app.template_folder or "templates", "index.html")


def load_serials():
    """Load valid serial numbers from CSV."""
    try:
        df = pd.read_csv(CSV_FILE)
        return set(df["serial_number"].astype(str))
    except Exception as e:
        print("Error reading CSV:", e)
        return set()


@app.route("/")
def index():
    # Check if the index.html template exists before rendering
    if not os.path.exists(TEMPLATE_FILE):
        # Log and return a friendly message instead of crashing
        print(f"❌ Template not found: {TEMPLATE_FILE}")
        return (
            "<h3 style='color:red;text-align:center'>"
            "Error: index.html template not found. "
            "Please ensure it is in the /templates folder.</h3>",
            500,
        )

    try:
        return render_template("index.html")
    except Exception as e:
        print(f"❌ Failed to render template: {e}")
        return (
            "<h3 style='color:red;text-align:center'>"
            "Error loading index.html — please check template syntax.</h3>",
            500,
        )


@app.route("/verify", methods=["POST"])
def verify():
    """Check if the scanned QR code is valid."""
    data = request.get_json()
    code = data.get("code", "").strip().upper()
    serials = load_serials()

    if code in serials:
        return jsonify({"status": "✅ Original Product", "valid": True})
    else:
        return jsonify({"status": "❌ Fake or Unknown Product", "valid": False})


if __name__ == "__main__":
    # Pre-start check to ensure index.html exists
    if not os.path.exists(TEMPLATE_FILE):
        print(f"⚠️  Warning: index.html not found at {TEMPLATE_FILE}.")
        print("   The site may return an error when accessed.")
    app.run(debug=True)
