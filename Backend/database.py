from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from urllib.parse import quote_plus
import os

# Load environment variables from .env
load_dotenv()

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# URL-encode the password to handle special characters
PASSWORD_ENCODED = quote_plus(PASSWORD) if PASSWORD else ""

# Construct the SQLAlchemy connection string with ENCODED password
DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD_ENCODED}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

# If using Supabase Transaction Pooler (Port 6543), add prepared_statement=false to prevent errors
if PORT == "6543":
    DATABASE_URL += "&prepare_threshold=0"

# Create the SQLAlchemy engine with connection pooling optimized for Supabase
# These settings help prevent timeout issues on Render
engine = create_engine(
    DATABASE_URL,
    pool_size=5,                    # Number of connections to maintain in the pool
    max_overflow=10,                # Additional connections that can be created when pool is full
    pool_timeout=30,                # Timeout for getting a connection from the pool
    pool_recycle=3600,              # Recycle connections after 1 hour (3600 seconds)
    pool_pre_ping=True,             # Test connections before using them (prevents stale connections)
    connect_args={
        "connect_timeout": 10,      # Connection timeout in seconds
        "keepalives": 1,            # Enable TCP keepalive
        "keepalives_idle": 30,      # Seconds before starting keepalive probes
        "keepalives_interval": 10,  # Interval between keepalive probes
        "keepalives_count": 5       # Number of keepalive probes before giving up
    },
    echo=False                      # Set to True for SQL query logging (debugging)
)

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for declarative models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
