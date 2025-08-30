#!/usr/bin/env python3
"""
Database migration script to update schema for chat history
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.models.models import engine, Base
from backend.core.config import DATABASE_URL
from sqlalchemy import text

def migrate_database():
    """Migrate database to new schema"""
    print("🔄 Starting database migration...")
    
    try:
        # Connect to database using SQLAlchemy
        with engine.connect() as conn:
            # Drop existing tables
            print("🗑️ Dropping existing tables...")
            Base.metadata.drop_all(bind=engine)
            
            # Recreate tables with new schema
            print("🏗️ Recreating tables with new schema...")
            Base.metadata.create_all(bind=engine)
            
            conn.commit()
        
        print("✅ Database migration completed successfully!")
        print("\n📋 What was updated:")
        print("- chat_history.session_id changed from INTEGER to VARCHAR(255)")
        print("- All tables recreated with proper relationships")
        print("- Ready for UUID-based chat sessions")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1) 