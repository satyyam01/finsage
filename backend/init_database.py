#!/usr/bin/env python3
"""
Database initialization script for FinSage PostgreSQL database
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.models import create_tables, engine
from backend.config import DATABASE_URL
import psycopg2
from sqlalchemy.exc import OperationalError

def test_connection():
    """Test database connection"""
    try:
        # Test with psycopg2 first
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        print("✅ PostgreSQL connection successful")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

def create_database():
    """Create database if it doesn't exist"""
    try:
        # Extract database name from URL
        db_name = DATABASE_URL.split('/')[-1]
        base_url = '/'.join(DATABASE_URL.split('/')[:-1])
        
        # Connect to PostgreSQL server (not specific database)
        conn = psycopg2.connect(base_url + '/postgres')
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"✅ Database '{db_name}' created successfully")
        else:
            print(f"✅ Database '{db_name}' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
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
    print("🚀 Initializing FinSage PostgreSQL Database...")
    print(f"📊 Database URL: {DATABASE_URL}")
    
    # Step 1: Test connection
    if not test_connection():
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your DATABASE_URL in .env file")
        print("3. Verify database credentials")
        print("4. Ensure database exists")
        return False
    
    # Step 2: Create database if needed
    if not create_database():
        return False
    
    # Step 3: Create tables
    if not create_tables_safe():
        return False
    
    print("\n🎉 Database initialization completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update your .env file with database credentials")
    print("2. Run the application to test the new database")
    print("3. Migrate existing data if needed")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 