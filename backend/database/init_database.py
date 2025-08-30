#!/usr/bin/env python3
"""
Database initialization script for FinSage SQLite database
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.models.models import create_tables, engine
from backend.core.config import DATABASE_URL
from sqlalchemy.exc import OperationalError

def test_connection():
    """Test database connection"""
    try:
        # Test with SQLAlchemy
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print("✅ SQLite connection successful")
        return True
    except Exception as e:
        print(f"❌ SQLite connection failed: {e}")
        return False

def create_tables_safe():
    """Create tables safely"""
    try:
        create_tables()
        print("✅ Database tables created successfully")
        return True
    except OperationalError as e:
        print(f"❌ Database operation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main initialization function"""
    print("🚀 Initializing FinSage SQLite Database...")
    print(f"📊 Database URL: {DATABASE_URL}")
    
    # Step 1: Test connection
    if not test_connection():
        print("\n💡 Troubleshooting tips:")
        print("1. Check your DATABASE_URL in .env file")
        print("2. Ensure the database directory is writable")
        print("3. Check file permissions")
        return False
    
    # Step 2: Create tables
    if not create_tables_safe():
        return False
    
    print("\n🎉 Database initialization completed successfully!")
    print("\n📋 Next steps:")
    print("1. Run the application to test the new database")
    print("2. The database file will be created automatically")
    
    return True

if __name__ == "__main__":
    main() 