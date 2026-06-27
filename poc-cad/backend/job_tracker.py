"""
Simple job tracking using JSON files instead of database
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

JOBS_DIR = Path("./jobs")
JOBS_DIR.mkdir(exist_ok=True)


class JobTracker:
    @staticmethod
    def create_job(job_id: str, job_type: str) -> Dict[str, Any]:
        """Create a new job"""
        job = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "pending",
            "progress": 0,
            "cad_specification": None,
            "file_path": None,
            "file_format": "STEP",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        JobTracker._save_job(job)
        return job

    @staticmethod
    def update_job(job_id: str, status: Optional[str] = None, progress: Optional[int] = None,
                   cad_specification: Optional[str] = None, file_path: Optional[str] = None,
                   file_format: Optional[str] = None) -> Optional[Dict]:
        """Update job status"""
        job = JobTracker.get_job(job_id)
        if not job:
            return None

        if status:
            job["status"] = status
        if progress is not None:
            job["progress"] = progress
        if cad_specification:
            job["cad_specification"] = cad_specification
        if file_path:
            job["file_path"] = file_path
        if file_format:
            job["file_format"] = file_format

        job["updated_at"] = datetime.utcnow().isoformat()
        JobTracker._save_job(job)
        return job

    @staticmethod
    def get_job(job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        job_file = JOBS_DIR / f"{job_id}.json"
        if job_file.exists():
            with open(job_file) as f:
                return json.load(f)
        return None

    @staticmethod
    def _save_job(job: Dict[str, Any]) -> None:
        """Save job to file"""
        job_file = JOBS_DIR / f"{job['job_id']}.json"
        with open(job_file, 'w') as f:
            json.dump(job, f, indent=2)


# Fake database dependency for compatibility
class FakeDB:
    pass


def get_db():
    """Fake dependency for FastAPI"""
    return FakeDB()
