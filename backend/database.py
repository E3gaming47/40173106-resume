from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables from .env file (if exists)
load_dotenv()

# Check for MSSQL connection variables (Liara MSSQL database)
DB_USER = os.getenv("DB_USER")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_PASS = os.getenv("DB_PASS")

# Determine database URL
if DB_USER and DB_NAME and DB_HOST and DB_PORT and DB_PASS:
    # Use MSSQL if all required variables are set
    SQLALCHEMY_DATABASE_URL = (
        f"mssql+pyodbc://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    )
    connect_args = {}
elif os.getenv("DATABASE_URL"):
    # Use provided DATABASE_URL (for PostgreSQL, etc.)
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
    connect_args = {}
else:
    # Fallback to SQLite - use /tmp for writable directory in containers
    # Liara containers need a writable path
    db_file = "resume.db"
    
    # Try multiple paths for SQLite
    possible_paths = [
        "/tmp/resume.db",  # Preferred for containers
        "./resume.db",     # Fallback to current directory
        "resume.db"        # Last resort
    ]
    
    # Use /tmp if it exists and is writable, otherwise use current directory
    import os
    if os.path.exists("/tmp") and os.access("/tmp", os.W_OK):
        SQLALCHEMY_DATABASE_URL = f"sqlite:////tmp/{db_file}"
    else:
        # Try to create /tmp if it doesn't exist
        try:
            os.makedirs("/tmp", exist_ok=True)
            if os.access("/tmp", os.W_OK):
                SQLALCHEMY_DATABASE_URL = f"sqlite:////tmp/{db_file}"
            else:
                SQLALCHEMY_DATABASE_URL = f"sqlite:///./{db_file}"
        except:
            SQLALCHEMY_DATABASE_URL = f"sqlite:///./{db_file}"
    
    connect_args = {"check_same_thread": False}

# Create engine with lazy connection (doesn't connect until first use)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args=connect_args,
    pool_pre_ping=True  # Verify connections before using
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

