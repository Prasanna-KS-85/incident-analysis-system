import pymongo
from datetime import datetime
import streamlit as st
import certifi  # Helps with SSL errors on some networks

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
# UPDATED: Using your specific credentials and cluster
# Note: Special characters in password (like @) are safe here because it's a string,
# but if connection fails, we might need to URL-encode the password. Let's try direct first.
MONGO_URI = "mongodb+srv://admin:6369127191%40Aa@cluster0.fq8d3wm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

DB_NAME = "civic_sentinel_db"
COLLECTION_NAME = "grievances"

class DatabaseHandler:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self.is_connected = False
        
        try:
            # Connect to MongoDB
            # We add tlsCAFile=certifi.where() to prevent SSL Certificate errors on secure networks (like college WiFi)
            self.client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
            
            # Trigger a connection check
            self.client.admin.command('ping')
            
            self.db = self.client[DB_NAME]
            self.collection = self.db[COLLECTION_NAME]
            self.is_connected = True
            print("✅ DATABASE: Connected via MongoDB Atlas.")
            
        except Exception as e:
            print(f"⚠️ DATABASE ERROR: Could not connect to Cloud.")
            print(f"   Error Details: {e}")
            print("   -> System will run in 'Offline Mode' (Data won't be saved).")
            self.is_connected = False

    def submit_complaint(self, data_packet):
        """
        Saves a complaint from the User App.
        """
        if not self.is_connected:
            return False, "Database Offline"
        
        try:
            # Add Server-Side Metadata
            data_packet['server_timestamp'] = datetime.utcnow()
            data_packet['status'] = "Pending"
            
            # Insert into DB
            result = self.collection.insert_one(data_packet)
            return True, str(result.inserted_id)
        except Exception as e:
            return False, str(e)

    def fetch_all_complaints(self):
        """
        Retrieves all complaints for the Admin Dashboard.
        """
        if not self.is_connected:
            return []
        
        try:
            # Fetch latest first
            cursor = self.collection.find().sort("server_timestamp", -1)
            return list(cursor)
        except Exception as e:
            print(f"Fetch Error: {e}")
            return []

    def clear_all_complaints(self):
        """
        DANGER: Deletes ALL documents in the grievances collection.
        Used for system reset/testing.
        """
        if self.collection is None:
            return False
        try:
            # Deletes everything in the collection
            result = self.collection.delete_many({})
            print(f"⚠️ SYSTEM RESET: Deleted {result.deleted_count} records.")
            return True
        except Exception as e:
            print(f"Error clearing DB: {e}")
            return False

    def verify_truth(self, image_path, text_claim):
        """
        Placeholder for the AI Truth Verification logic.
        """
        pass

# --- TEST BLOCK (Runs only when you execute this file directly) ---
if __name__ == "__main__":
    print("🔌 Testing Database Connection...")
    db = DatabaseHandler()
    if db.is_connected:
        print("✅ SUCCESS: Connected to Cloud Database!")
    else:
        print("❌ FAILED: Check your password or IP whitelist.")