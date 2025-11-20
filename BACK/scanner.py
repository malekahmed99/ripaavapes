from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__)

# Database Configuration
# Use DATABASE_URL env var if available (for cloud), otherwise local sqlite file
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///serials.db')
# Fix for some cloud providers (like Heroku) using postgres:// instead of postgresql://
if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

CSV_FILE = "serials.csv"
TEMPLATE_FILE = os.path.join(app.template_folder or "templates", "index.html")

# Database Model
class Serial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(255), unique=True, nullable=False, index=True)
    used = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Serial {self.serial_number}>'

def init_db():
    """Initialize the database and seed from CSV if empty."""
    with app.app_context():
        db.create_all()
        
        # Check if we need to seed data
        if Serial.query.first() is None:
            print("Database empty. Seeding from CSV...")
            if os.path.exists(CSV_FILE):
                try:
                    df = pd.read_csv(CSV_FILE, dtype={"serial_number": str, "used": int})
                    # Ensure columns exist
                    if "serial_number" in df.columns:
                        # Bulk insert for performance
                        serials_to_add = []
                        for _, row in df.iterrows():
                            # Handle potential missing 'used' column in CSV by defaulting to 0
                            used_val = int(row['used']) if 'used' in df.columns and pd.notna(row['used']) else 0
                            serials_to_add.append(Serial(serial_number=str(row['serial_number']).strip().upper(), used=used_val))
                        
                        db.session.add_all(serials_to_add)
                        db.session.commit()
                        print(f"Successfully seeded {len(serials_to_add)} serials.")
                    else:
                        print("CSV missing 'serial_number' column. Skipping seed.")
                except Exception as e:
                    print(f"Error seeding database from CSV: {e}")
            else:
                print(f"No {CSV_FILE} found. Starting with empty database.")
        else:
            print("Database already contains data. Skipping seed.")

def verify_and_mark(serial):
    """
    Verify the serial and mark it as used if it is valid and unused.
    Returns a tuple (valid: bool, message: str).
    """
    s = serial.strip().upper()
    if not s:
        return False, "Empty serial"

    # Find serial in DB
    serial_record = Serial.query.filter_by(serial_number=s).first()

    if not serial_record:
        return False, "❌ Fake or Unknown Product"

    if serial_record.used == 1:
        return False, "⚠️ Serial already used"

    # Mark used
    try:
        serial_record.used = 1
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Error updating database:", e)
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

# Health check endpoint for cloud platforms
@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    # Pre-start check to ensure index.html exists
    if not os.path.exists(TEMPLATE_FILE):
        print(f"⚠️  Warning: index.html not found at {TEMPLATE_FILE}.")
        print("   The site may return an error when accessed.")
    
    # Initialize DB
    if not os.environ.get("TESTING"):
        init_db()
    
    app.run(debug=True)
else:
    # When running with gunicorn, we need to init db too.
    if not os.environ.get("TESTING"):
        init_db()

