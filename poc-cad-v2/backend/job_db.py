"""
Job storage and tracking using SQLAlchemy ORM
"""
import os
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./jobs.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class JobModel(Base):
    """Job tracking model"""
    __tablename__ = "jobs"
    
    job_id = Column(String, primary_key=True, index=True)
    job_type = Column(String, index=True)
    status = Column(String, default="pending")
    progress = Column(Integer, default=0)
    cad_specification = Column(Text, nullable=True)
    file_path = Column(String, nullable=True)
    file_format = Column(String, default="STEP")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Create tables
Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_job(db, job_id: str, job_type: str) -> JobModel:
    """Create a new job"""
    job = JobModel(job_id=job_id, job_type=job_type, status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def update_job(db, job_id: str, status: str = None, progress: int = None, 
               cad_specification: str = None, file_path: str = None) -> JobModel:
    """Update job status"""
    job = db.query(JobModel).filter(JobModel.job_id == job_id).first()
    if job:
        if status:
            job.status = status
        if progress is not None:
            job.progress = progress
        if cad_specification:
            job.cad_specification = cad_specification
        if file_path:
            job.file_path = file_path
        job.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
    return job


def get_job(db, job_id: str) -> JobModel:
    """Get job by ID"""
    return db.query(JobModel).filter(JobModel.job_id == job_id).first()
