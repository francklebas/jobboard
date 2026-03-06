import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://user:password@postgres:5432/jobboard_db")

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    company = Column(String(255))
    location = Column(String(255))
    url = Column(String(255), unique=True, index=True)
    source = Column(String(255))
    date_posted = Column(String(255)) # Storing as string for now, can be converted to DateTime if needed
    description = Column(Text)

class LastSync(Base):
    __tablename__ = "last_sync"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
    except OperationalError as e:
        print(f"Database connection failed: {e}")
        print("Please ensure the PostgreSQL service is running and accessible.")
        raise

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def store_jobs(jobs_data: list[dict]) -> int:
    db = SessionLocal()
    try:
        # Clear existing jobs
        db.query(Job).delete()
        db.commit()

        # Add new jobs
        new_jobs = []
        for job_data in jobs_data:
            job = Job(**job_data)
            db.add(job)
            new_jobs.append(job)
        db.commit()
        return len(new_jobs)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_all_jobs() -> list[dict]:
    db = SessionLocal()
    try:
        jobs = db.query(Job).all()
        return [{
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "url": j.url,
            "source": j.source,
            "date_posted": j.date_posted,
            "description": j.description,
        } for j in jobs]
    finally:
        db.close()

def get_last_sync() -> str | None:
    db = SessionLocal()
    try:
        last_sync_entry = db.query(LastSync).order_by(LastSync.timestamp.desc()).first()
        if last_sync_entry:
            return last_sync_entry.timestamp.isoformat()
        return None
    finally:
        db.close()

def set_last_sync(ts: str):
    db = SessionLocal()
    try:
        # Clear previous last sync entries (optional, or keep a history)
        db.query(LastSync).delete()
        db.commit()

        new_sync = LastSync(timestamp=datetime.fromisoformat(ts))
        db.add(new_sync)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
