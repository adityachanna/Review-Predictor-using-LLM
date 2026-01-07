# Supabase Connection Issue - Resolution Guide

## Problem
Your FastAPI application on Render was experiencing connection timeouts when trying to connect to Supabase PostgreSQL database:
```
psycopg2.OperationalError: connection to server at "aws-1-ap-southeast-1.pooler.supabase.com" (13.213.241.248), port 5432 failed: Connection timed out
```

## Solutions Implemented

### 1. ✅ Fixed Password Encoding
**Issue**: The connection string was using the raw password instead of the URL-encoded version.

**Fixed in `database.py` line 22**:
```python
# Before (WRONG):
DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

# After (CORRECT):
DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD_ENCODED}@{HOST}:{PORT}/{DBNAME}?sslmode=require"
```

### 2. ✅ Added Connection Pooling
**Issue**: No connection pool configuration was causing connection instability on Render.

**Added settings**:
- `pool_size=5`: Maintains 5 persistent connections
- `max_overflow=10`: Can create up to 10 additional connections when needed
- `pool_timeout=30`: Waits up to 30 seconds for a connection from the pool
- `pool_recycle=3600`: Recycles connections after 1 hour to prevent stale connections
- `pool_pre_ping=True`: Tests connections before using them (critical for preventing timeout errors)

### 3. ✅ Added TCP Keepalive Settings
**Issue**: Long-running connections were being dropped silently.

**Added settings**:
```python
connect_args={
    "connect_timeout": 10,      # Connection timeout in seconds
    "keepalives": 1,            # Enable TCP keepalive
    "keepalives_idle": 30,      # Seconds before starting keepalive probes
    "keepalives_interval": 10,  # Interval between keepalive probes
    "keepalives_count": 5       # Number of keepalive probes before giving up
}
```

## Additional Recommendations

### Option A: Switch to Transaction Pooler (Recommended for Render)

**Update your `.env` file** to use Transaction Pooler instead of Session Pooler:

```env
user=postgres.qibdynpydojobdnkkxbc
password=[YOUR-PASSWORD]
host=aws-1-ap-southeast-1.pooler.supabase.com
port=6543  # ← Change from 5432 to 6543
dbname=postgres
```

**Why Transaction Pooler?**
- Better for serverless/cloud deployments like Render
- More efficient connection handling
- Less likely to timeout
- Already handled in `database.py` (adds `prepare_threshold=0` automatically)

### Option B: Use Direct Connection (Alternative)

If Transaction Pooler doesn't work, try Direct Connection:

```env
user=postgres.qibdynpydojobdnkkxbc
password=[YOUR-PASSWORD]
host=aws-1-ap-southeast-1.connect.supabase.com  # ← Changed subdomain
port=5432
dbname=postgres
```

**Note**: Direct Connection uses IPv6, which Render supports.

### Option C: Add Environment Variables to Render

Make sure your Render environment variables are set correctly:

1. Go to your Render Dashboard
2. Select your service
3. Go to "Environment" tab
4. Add these variables:
   ```
   user=postgres.qibdynpydojobdnkkxbc
   password=[YOUR-PASSWORD]
   host=aws-1-ap-southeast-1.pooler.supabase.com
   port=6543
   dbname=postgres
   ```

### Option D: Add Retry Logic (Extra Safety)

Consider adding retry logic to your API endpoints. Example for `api.py`:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def submit_review_with_retry(data: ReviewCreate, db: Session):
    # Your existing logic here
    pass
```

Install tenacity:
```bash
pip install tenacity
```

## Testing the Fix

### 1. Test Locally

Create a test file `Backend/test_connection.py`:

```python
from database import engine

try:
    with engine.connect() as connection:
        result = connection.execute("SELECT 1")
        print("✅ Connection successful!")
        print(f"Result: {result.fetchone()}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

Run it:
```bash
cd Backend
python test_connection.py
```

### 2. Deploy to Render

1. Commit your changes:
   ```bash
   git add Backend/database.py
   git commit -m "Fix: Add connection pooling and timeout settings for Supabase"
   git push
   ```

2. Render will auto-deploy (if configured)

3. Check logs in Render Dashboard for connection success

## Monitoring

### Check Connection Pool Status

Add this endpoint to monitor your connection pool health:

```python
# Add to api.py

@router.get("/health/database")
def database_health(db: Session = Depends(get_db)):
    """Check database connection health"""
    try:
        # Simple query to test connection
        db.execute("SELECT 1")
        
        # Get pool status
        pool = engine.pool
        
        return {
            "status": "healthy",
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database unhealthy: {str(e)}")
```

## Common Issues & Solutions

### Issue: Still getting timeouts
**Solution**: Switch to Transaction Pooler (port 6543)

### Issue: "too many connections"
**Solution**: Reduce `pool_size` to 3 and `max_overflow` to 5

### Issue: "SSL error"
**Solution**: Make sure `?sslmode=require` is in your connection string

### Issue: Password has special characters
**Solution**: Already fixed! We're using `PASSWORD_ENCODED` now

## Resources

- [Supabase Database Connections](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [Render PostgreSQL Guide](https://render.com/docs/databases)

## Summary

The main changes were:
1. ✅ Use encoded password in connection string
2. ✅ Add connection pooling with pre-ping
3. ✅ Add TCP keepalive settings
4. 💡 Recommend switching to Transaction Pooler (port 6543)

Test locally first, then deploy to Render!
