from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
from pathlib import Path
from dotenv import load_dotenv
from models import UserRegister, UserLogin, Token, PromptRequest, JobResponse
from cad_service import generate_cad_from_image, generate_cad_from_prompt
from cad_cadquery_executor import generate_cad_from_code
from job_tracker import JobTracker
from auth_storage import AuthManager
import json
import uuid

load_dotenv()

app = FastAPI(
    title="CAD Generation API",
    description="AI-Assisted CAD Model Generation Platform",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
UPLOAD_DIR = Path("./uploads")
OUTPUT_DIR = Path("./cad_models")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


# Routes
@app.get("/")
async def root():
    return {"message": "CAD Generation API v1.0"}


@app.post("/auth/register")
async def register(user_data: UserRegister):
    """Register a new user"""
    user_dict = user_data.dict()
    result = AuthManager.register_user(user_dict)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return result


@app.post("/auth/login")
async def login(user_data: UserLogin):
    """User login"""
    result = AuthManager.login(user_data.email, user_data.password)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=401, detail=result.get("message"))
    
    return result


@app.post("/auth/forgot-password")
async def forgot_password(email: str):
    """Request password reset"""
    return {"message": "Password reset email sent"}


@app.post("/cad/generate-from-prompt")
async def generate_from_prompt(request: PromptRequest):
    """Generate CAD from text prompt using Claude AI"""
    try:
        job_id = str(uuid.uuid4())
        job_dir = OUTPUT_DIR / job_id
        
        # Create job tracker entry
        JobTracker.create_job(job_id, "prompt")
        JobTracker.update_job(job_id, status="processing", progress=10)
        
        # Generate OpenSCAD code from Claude (Code-as-CAD pipeline)
        result = await generate_cad_from_prompt(request.prompt)
        JobTracker.update_job(job_id, progress=50)
        
        if result.get("status") == "failed":
            JobTracker.update_job(job_id, status="failed")
            return {
                "status": "error",
                "job_id": job_id,
                "error": result.get("error", "Unknown error")
            }
        
        code = result.get("code")
        code_type = result.get("code_type", "openscad")
        
        # Prepare code spec for executor
        code_spec = json.dumps({
            "code": code,
            "code_type": code_type,
            "title": "Generated CAD Model"
        })
        
        # Execute OpenSCAD code to generate STL
        file_path = generate_cad_from_code(code_spec, job_dir)
        JobTracker.update_job(job_id, progress=80, cad_specification=code[:500] + "...")
        
        if not file_path:
            JobTracker.update_job(job_id, status="failed")
            return {
                "status": "error",
                "job_id": job_id,
                "error": "Failed to generate CAD model"
            }
        
        # Update to completed
        JobTracker.update_job(job_id, status="completed", progress=100, file_path=file_path, file_format="STL")
        
        return {
            "status": "completed",
            "job_id": job_id,
            "code_preview": code[:200] + "...",
            "model_format": "STL",
            "file_path": file_path,
            "file_url": f"/cad/download/{job_id}" if file_path else None
        }
    except Exception as e:
        print(f"Error in generate_from_prompt: {e}")
        import traceback
        traceback.print_exc()
        JobTracker.update_job(job_id, status="failed")
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/cad/generate-from-image")
async def generate_from_image(file: UploadFile = File(...)):
    """Generate CAD from reference image using Claude Vision AI (Code-as-CAD)"""
    try:
        job_id = str(uuid.uuid4())
        job_dir = OUTPUT_DIR / job_id
        
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # Create job tracker entry
        JobTracker.create_job(job_id, "image")
        JobTracker.update_job(job_id, status="processing", progress=10)
        
        # Generate OpenSCAD code from Claude Vision (Code-as-CAD pipeline)
        result = await generate_cad_from_image(str(file_path))
        JobTracker.update_job(job_id, progress=50)
        
        if result.get("status") == "failed":
            JobTracker.update_job(job_id, status="failed")
            return {
                "status": "error",
                "job_id": job_id,
                "error": result.get("error", "Unknown error")
            }
        
        code = result.get("code")
        code_type = result.get("code_type", "openscad")
        
        # Prepare code spec for executor
        code_spec = json.dumps({
            "code": code,
            "code_type": code_type,
            "title": "Generated CAD Model from Image"
        })
        
        # Execute OpenSCAD code to generate STL
        output_file_path = generate_cad_from_code(code_spec, job_dir)
        JobTracker.update_job(job_id, progress=80, cad_specification=code[:500] + "...")
        
        if not output_file_path:
            JobTracker.update_job(job_id, status="failed")
            return {
                "status": "error",
                "job_id": job_id,
                "error": "Failed to render OpenSCAD code"
            }
        
        # Update to completed
        JobTracker.update_job(job_id, status="completed", progress=100, file_path=output_file_path, file_format="STL")
        
        return {
            "status": "completed",
            "job_id": job_id,
            "file_uploaded": file.filename,
            "code_preview": code[:200] + "...",
            "model_format": "STL",
            "file_path": output_file_path,
            "file_url": f"/cad/download/{job_id}" if output_file_path else None
        }
    except Exception as e:
        print(f"Error in generate_from_image: {e}")
        import traceback
        traceback.print_exc()
        JobTracker.update_job(job_id, status="failed")
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/cad/generate-from-sketch")
async def generate_from_sketch(file: UploadFile = File(...)):
    """Generate CAD from hand-drawn sketch using Claude Vision AI (Code-as-CAD)"""
    try:
        job_id = str(uuid.uuid4())
        job_dir = OUTPUT_DIR / job_id
        
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # Create job tracker entry
        JobTracker.create_job(job_id, "sketch")
        JobTracker.update_job(job_id, status="processing", progress=10)
        
        # Generate OpenSCAD code from Claude Vision (Code-as-CAD pipeline)
        result = await generate_cad_from_image(str(file_path))
        JobTracker.update_job(job_id, progress=50)
        
        if result.get("status") == "failed":
            JobTracker.update_job(job_id, status="failed")
            return {
                "status": "error",
                "job_id": job_id,
                "error": result.get("error", "Unknown error")
            }
        
        code = result.get("code")
        code_type = result.get("code_type", "openscad")
        
        # Prepare code spec for executor
        code_spec = json.dumps({
            "code": code,
            "code_type": code_type,
            "title": "Generated CAD Model from Sketch"
        })
        
        # Execute OpenSCAD code to generate STL
        output_file_path = generate_cad_from_code(code_spec, job_dir)
        JobTracker.update_job(job_id, progress=80, cad_specification=code[:500] + "...")
        
        if not output_file_path:
            JobTracker.update_job(job_id, status="failed")
            return {
                "status": "error",
                "job_id": job_id,
                "error": "Failed to render OpenSCAD code"
            }
        
        # Update to completed
        JobTracker.update_job(job_id, status="completed", progress=100, file_path=output_file_path, file_format="STL")
        
        return {
            "status": "completed",
            "job_id": job_id,
            "sketch_uploaded": file.filename,
            "code_preview": code[:200] + "...",
            "model_format": "STL",
            "file_path": output_file_path,
            "file_url": f"/cad/download/{job_id}" if output_file_path else None
        }
    except Exception as e:
        print(f"Error in generate_from_sketch: {e}")
        import traceback
        traceback.print_exc()
        JobTracker.update_job(job_id, status="failed")
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/cad/upload-base-model")
async def upload_base_model(file: UploadFile = File(...)):
    """Upload existing CAD file (.STL, .STEP, .OBJ)"""
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    return {
        "status": "success",
        "file_uploaded": file.filename,
        "supported_formats": [".STL", ".STEP", ".OBJ"]
    }


@app.get("/cad/job/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a CAD generation job"""
    job = JobTracker.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job_id,
        "status": job.get("status"),
        "progress": job.get("progress"),
        "job_type": job.get("job_type"),
        "cad_specification": job.get("cad_specification"),
        "file_path": job.get("file_path"),
        "file_url": f"/cad/download/{job_id}" if job.get("file_path") else None,
        "created_at": job.get("created_at")
    }


@app.get("/cad/download/{job_id}")
async def download_cad(job_id: str):
    """Download generated CAD file"""
    job = JobTracker.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if not job.get("file_path") or not Path(job.get("file_path")).exists():
        raise HTTPException(status_code=404, detail="CAD file not available")
    
    file_path = job.get("file_path")
    file_ext = Path(file_path).suffix
    media_type = "model/step" if file_ext == ".step" else "model/stl"
    
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=f"model_{job_id}{file_ext}"
    )


@app.get("/projects")
async def list_projects():
    """List all projects"""
    return {"projects": []}


@app.get("/spaces")
async def list_spaces():
    """List all spaces"""
    return {"spaces": []}


@app.get("/catalogs")
async def list_catalogs():
    """List all catalogs"""
    return {"catalogs": []}


@app.get("/jobs")
async def list_jobs():
    """List all jobs"""
    jobs_dir = Path("./jobs")
    if not jobs_dir.exists():
        return {"jobs": []}
    
    jobs = []
    for job_file in jobs_dir.glob("*.json"):
        with open(job_file) as f:
            job = json.load(f)
            jobs.append({
                "job_id": job.get("job_id"),
                "job_type": job.get("job_type"),
                "status": job.get("status"),
                "progress": job.get("progress"),
                "created_at": job.get("created_at")
            })
    
    return {"jobs": jobs}


@app.get("/user/profile")
async def get_user_profile():
    """Get current user profile"""
    return {
        "user_id": "user_001",
        "name": "John Doe",
        "email": "john@example.com"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
