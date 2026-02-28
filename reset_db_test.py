import sys
import os

# Adjust path to find utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from utils.db_handler import DatabaseHandler

def test_reset():
    db = DatabaseHandler()
    if not db.is_connected:
        print("❌ DB Not Connected")
        return

    print("⚠️  Testing System Reset...")
    success = db.clear_all_complaints()
    if success:
        print("✅ System Reset Successful")
    else:
        print("❌ System Reset Failed")

if __name__ == "__main__":
    test_reset()
