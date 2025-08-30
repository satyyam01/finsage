#!/usr/bin/env python3
"""
Simple database initialization script
"""
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def init_database():
    """Initialize the database tables"""
    try:
        print("🚀 Initializing FinSage Database...")
        
        # Import required modules
        from backend.models.models import Base, engine
        from backend.core.config import DATABASE_URL
        
        print(f"📊 Database URL: {DATABASE_URL}")
        
        # Create all tables
        print("🏗️ Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database initialization completed successfully!")
        print("📁 Database file: users.db")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1) 