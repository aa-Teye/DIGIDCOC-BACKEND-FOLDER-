import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Defaults to a local SQLite file so the backend runs with zero setup. Point
# DATABASE_URL at a Supabase/Neon Postgres connection string when ready — swap is
# a one-line env change, no code change (see requirements.txt for the Postgres
# driver note).
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./digidoc.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
