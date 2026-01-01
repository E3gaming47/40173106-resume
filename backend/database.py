from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# SQLite database - use /tmp for writable directory in containers
# Liara containers need a writable path
db_url = os.getenv("DATABASE_URL", "")

if not db_url or db_url.startswith("sqlite"):
    # Use /tmp directory which is always writable in containers (Liara)
    # This ensures the database file can be created
    db_file = "resume.db"
    SQLALCHEMY_DATABASE_URL = f"sqlite:////tmp/{db_file}"
else:
    # Use provided DATABASE_URL (for PostgreSQL, etc.)
    SQLALCHEMY_DATABASE_URL = db_url

# SQLite connect_args only needed for SQLite
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

