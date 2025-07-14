#!/usr/bin/env python3
"""
Database migration script to update schema for chat history
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.models import engine, Base
from sqlalchemy import text
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://finsage_user:finsage_password@localhost:5432/finsage_db")

def migrate_database():
    """Migrate database to new schema"""
    print("🔄 Starting database migration...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Drop existing chat_history table
        print("🗑️ Dropping existing chat_history table...")
        cursor.execute("DROP TABLE IF EXISTS chat_history CASCADE")
        
        # Drop existing sessions table
        print("🗑️ Dropping existing sessions table...")
        cursor.execute("DROP TABLE IF EXISTS sessions CASCADE")
        
        # Drop existing loan_analyses table
        print("🗑️ Dropping existing loan_analyses table...")
        cursor.execute("DROP TABLE IF EXISTS loan_analyses CASCADE")
        
        # Drop existing users table
        print("🗑️ Dropping existing users table...")
        cursor.execute("DROP TABLE IF EXISTS users CASCADE")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Recreate tables with new schema
        print("🏗️ Recreating tables with new schema...")
        Base.metadata.create_all(bind=engine)
        
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