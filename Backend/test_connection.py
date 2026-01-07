from database import engine
from sqlalchemy import text

print("🔍 Testing Supabase database connection...")
print("=" * 50)

try:
    # Test connection
    with engine.connect() as connection:
        # Simple query
        result = connection.execute(text("SELECT 1 as test"))
        test_result = result.fetchone()
        
        print("✅ Connection successful!")
        print(f"   Test query result: {test_result}")
        
        # Get database version
        result = connection.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"   PostgreSQL version: {version[:50]}...")
        
        # Check current database
        result = connection.execute(text("SELECT current_database()"))
        current_db = result.fetchone()[0]
        print(f"   Current database: {current_db}")
        
        # Pool statistics
        pool = engine.pool
        print("\n📊 Connection Pool Status:")
        print(f"   Pool size: {pool.size()}")
        print(f"   Checked in: {pool.checkedin()}")
        print(f"   Checked out: {pool.checkedout()}")
        print(f"   Overflow: {pool.overflow()}")
        
        print("\n" + "=" * 50)
        print("✨ All tests passed! Database is ready.")
        
except Exception as e:
    print("❌ Connection failed!")
    print(f"   Error: {str(e)}")
    print("\n📝 Troubleshooting tips:")
    print("   1. Check your .env file has correct credentials")
    print("   2. Try switching to Transaction Pooler (port 6543)")
    print("   3. Verify your Supabase database is running")
    print("   4. Check if your password has special characters (should be URL-encoded)")
