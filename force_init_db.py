#!/usr/bin/env python3
"""
Force database initialization script - recreates all tables
"""
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def force_init_database():
    """Force initialize the database tables"""
    try:
        print("🚀 Force Initializing FinSage Database...")
        
        # Import required modules
        from backend.models.models import Base, engine
        from backend.core.config import DATABASE_URL
        
        print(f"📊 Database URL: {DATABASE_URL}")
        
        # Drop all tables first
        print("🗑️ Dropping existing tables...")
        Base.metadata.drop_all(bind=engine)
        
        # Create all tables
        print("🏗️ Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database force initialization completed successfully!")
        print("📁 Database file: users.db")
        
        # Test the tables
        print("🧪 Testing table creation...")
        from sqlalchemy import text
        with engine.connect() as conn:
            # Check if users table exists
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'"))
            if result.fetchone():
                print("✅ Users table created successfully")
            else:
                print("❌ Users table not found")
            
            # List all tables
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 All tables: {tables}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = force_init_database()
    sys.exit(0 if success else 1) 