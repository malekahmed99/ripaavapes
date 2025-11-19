from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import tempfile

app = Flask(__name__)
CSV_FILE = "serials.csv"
TEMPLATE_FILE = os.path.join(app.template_folder or "templates", "index.html")


def ensure_csv_has_used_column():
    """Ensure CSV exists and has 'serial_number' and 'used' columns."""
    if not os.path.exists(CSV_FILE):
        # create an empty csv with headers
        df = pd.DataFrame(columns=["serial_number", "used"])
        df.to_csv(CSV_FILE, index=False)


def load_serials_df():
    """Load the serials DataFrame safely."""
    ensure_csv_has_used_column()
    try:
        df = pd.read_csv(CSV_FILE, dtype={"serial_number": str, "used": int})
        return df
    except Exception as e:
        print("Error reading CSV:", e)
        # Return empty df with correct columns
        return pd.DataFrame(columns=["serial_number", "used"])


def verify_and_mark(serial):
    """
    Verify the serial and mark it as used if it is valid and unused.
    Returns a tuple (valid: bool, message: str).
    """
    s = serial.strip().upper()
    if not s:
        return False, "Empty serial"

    df = load_serials_df()

    # find rows where serial matches (case-insensitive)
    match_idx = df.index[df["serial_number"].astype(str).str.strip().str.upper() == s].tolist()

    if not match_idx:
        return False, "❌ Fake or Unknown Product"

    idx = match_idx[0]
    used_val = int(df.at[idx, "used"]) if "used" in df.columns and pd.notna(df.at[idx, "used"]) else 0

    if used_val == 1:
        return False, "⚠️ Serial already used"

    # mark used and save atomically
    try:
        df.at[idx, "used"] = 1
        # write to temporary file then replace to reduce risk of corruption
        dirn = os.path.dirname(os.path.abspath(CSV_FILE)) or "."
        with tempfile.NamedTemporaryFile(mode="w", delete=False, dir=dirn, newline="") as tmpf:
            tmp_path = tmpf.name
            df.to_csv(tmp_path, index=False)
        os.replace(tmp_path, CSV_FILE)
    except Exception as e:
        print("Error updating CSV:", e)
        return False, "⚠️ Verification failed (server error)"

    return True, "✅ Original Product (first scan — marked as used)"


@app.route("/")
def index():
    # Check if the index.html template exists before rendering
    if not os.path.exists(TEMPLATE_FILE):
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
    """Check if the scanned QR code is valid and mark it used on first successful verification."""
    data = request.get_json(force=True, silent=True) or {}
    code = (data.get("code", "") or "").strip().upper()
    if not code:
        return jsonify({"status": "Invalid request", "valid": False}), 400

    valid, message = verify_and_mark(code)
    return jsonify({"status": message, "valid": valid})


if __name__ == "__main__":
    # Pre-start check to ensure index.html exists
    if not os.path.exists(TEMPLATE_FILE):
        print(f"⚠️  Warning: index.html not found at {TEMPLATE_FILE}.")
        print("   The site may return an error when accessed.")
    ensure_csv_has_used_column()
    app.run(debug=True)
