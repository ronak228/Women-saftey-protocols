from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()

# MongoDB Atlas connection string
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://22it027:<db_password>@cluster0.wcr45.mongodb.net/womensafety?retryWrites=true&w=majority&connectTimeoutMS=5000')

# Create MongoDB client with timeout
client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)

# Get database
db = client.womensafety

# Collections
users = db.users
volunteers = db.volunteers
emergency_contacts = db.emergency_contacts
safety_tips = db.safety_tips

def init_db():
    """Initialize database with some default data"""
    try:
        # Test the connection
        client.server_info()
        print("Successfully connected to MongoDB!")
        
        # Add default safety tips if collection is empty
        if safety_tips.count_documents({}) == 0:
            default_tips = [
                {
                    "title": "Stay Alert",
                    "description": "Always be aware of your surroundings and trust your instincts.",
                    "category": "general"
                },
                {
                    "title": "Emergency Contacts",
                    "description": "Keep important emergency numbers saved in your phone.",
                    "category": "preparation"
                },
                {
                    "title": "Share Location",
                    "description": "Share your location with trusted friends or family when traveling.",
                    "category": "technology"
                }
            ]
            safety_tips.insert_many(default_tips)
            print("Default safety tips added successfully!")
    except ConnectionFailure:
        print("Failed to connect to MongoDB. Please check your connection string and network connection.")
        raise

def get_db():
    """Get database instance"""
    return db

def close_db():
    """Close database connection"""
    client.close() 