import unittest
import os
import tempfile

# Create a temp file for the database
db_fd, db_path = tempfile.mkstemp()
os.close(db_fd)

# Set testing flag and database URL before import
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

from scanner import app, db, Serial, init_db

class ScannerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        
        # Create tables and seed data
        with app.app_context():
            db.create_all()
            # Add a test serial
            db.session.add(Serial(serial_number="TEST1234", used=0))
            db.session.add(Serial(serial_number="USED1234", used=1))
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    @classmethod
    def tearDownClass(cls):
        # Clean up the temp file after all tests
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_health(self):
        rv = self.app.get('/health')
        self.assertEqual(rv.status_code, 200)

    def test_verify_valid_unused(self):
        rv = self.app.post('/verify', json={'code': 'TEST1234'})
        json_data = rv.get_json()
        self.assertTrue(json_data['valid'])
        self.assertIn("Original Product", json_data['status'])
        
        # Verify it is now marked as used in DB
        with app.app_context():
            serial = Serial.query.filter_by(serial_number="TEST1234").first()
            self.assertEqual(serial.used, 1)

    def test_verify_valid_used(self):
        rv = self.app.post('/verify', json={'code': 'USED1234'})
        json_data = rv.get_json()
        self.assertFalse(json_data['valid'])
        self.assertIn("already used", json_data['status'])

    def test_verify_invalid(self):
        rv = self.app.post('/verify', json={'code': 'FAKE1234'})
        json_data = rv.get_json()
        self.assertFalse(json_data['valid'])
        self.assertIn("Fake or Unknown", json_data['status'])

    def test_init_db_imports_csv(self):
        # Create a dummy CSV
        csv_path = "serials.csv"
        with open(csv_path, "w") as f:
            f.write("serial_number,used\nIMPORT1,0\nIMPORT2,1\n")
        
        try:
            # Clear DB first
            with app.app_context():
                db.drop_all()
                
            # Run init_db
            init_db()
            
            # Verify data
            with app.app_context():
                s1 = Serial.query.filter_by(serial_number="IMPORT1").first()
                s2 = Serial.query.filter_by(serial_number="IMPORT2").first()
                self.assertIsNotNone(s1)
                self.assertEqual(s1.used, 0)
                self.assertIsNotNone(s2)
                self.assertEqual(s2.used, 1)
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    @classmethod
    def tearDownClass(cls):
        # Dispose engine to release file lock
        with app.app_context():
            db.engine.dispose()
            
        # Clean up the temp file after all tests
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except PermissionError:
                pass # Ignore if still locked

if __name__ == '__main__':
    unittest.main()
