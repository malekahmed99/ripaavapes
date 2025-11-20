import csv
import uuid
import qrcode
from pathlib import Path

# Configuration
OUTPUT_CSV = "serials.csv"
QR_FOLDER = Path("qrcodes")
NUM_SERIALS = 1000  # change how many you want

QR_FOLDER.mkdir(exist_ok=True)

def generate_serial():
    """Generate a unique serial (e.g., 12-character uppercase hex)."""
    return uuid.uuid4().hex[:12].upper()

def main():
    serials = [generate_serial() for _ in range(NUM_SERIALS)]

    # Save to CSV
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["serial_number"])
        for s in serials:
            writer.writerow([s])

    print(f"✅ Generated {NUM_SERIALS} serials and saved to {OUTPUT_CSV}")

    # Generate QR codes for each
    for s in serials:
        img = qrcode.make(s)
        img.save(QR_FOLDER / f"{s}.png")

    print(f"✅ QR codes saved in folder '{QR_FOLDER}'")

if __name__ == "__main__":
    main()
