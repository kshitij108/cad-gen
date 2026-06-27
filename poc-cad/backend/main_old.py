from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from pathlib import Path
from dotenv import load_dotenv
from models import UserRegister, UserLogin, Token, PromptRequest
from cad_service import generate_cad_from_image, generate_cad_from_prompt
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

# Create upload directory
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# Routes
@app.get("/")
async def root():
    return {"message": "CAD Generation API v1.0"}


@app.post("/auth/register")
async def register(user_data: UserRegister):
    """Register a new user"""
    return {
        "status": "success",
        "message": "User registered successfully",
        "user_id": "placeholder",
        "email": user_data.email
    }


@app.post("/auth/login")
async def login(user_data: UserLogin):
    """User login"""
    return {
        "status": "success",
        "access_token": "placeholder_token",
        "token_type": "bearer",
        "email": user_data.email
    }


@app.post("/auth/forgot-password")
async def forgot_password(email: str):
    """Request password reset"""
    return {"message": "Password reset email sent"}


@app.post("/cad/generate-from-prompt")
async def generate_from_prompt(request: PromptRequest):
    """Generate CAD from text prompt using Claude AI"""
    try:
        job_id = str(uuid.uuid4())
        result = await generate_cad_from_prompt(request.prompt)
        
        if result.get("status") == "failed":
            return {
                "status": "error",
                "job_id": job_id,
                "error": result.get("error", "Unknown error")
            }
        
        return {
            "status": "completed",
            "job_id": job_id,
            "cad_specification": result.get("cad_description"),
            "model_format": result.get("model_format", "STEP")
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/cad/generate-from-image")
async def generate_from_image(file: UploadFile = File(...)):
    """Generate CAD from reference image using Gemini Vision AI"""
    try:
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        job_id = str(uuid.uuid4())
        result = await generate_cad_from_image(str(file_path))
        
        if result.get("status") == "failed":
            return {
                "status": "error",
                "job_id": job_id,
                "error": result.get("error", "Unknown error")
            }
        
        return {
            "status": "completed",
            "job_id": job_id,
            "file_uploaded": file.filename,
            "cad_specification": result.get("cad_description"),
            "model_format": result.get("model_format", "STEP")
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/cad/generate-from-sketch")
async def generate_from_sketch(file: UploadFile = File(...)):
    """Generate CAD from hand-drawn sketch using Gemini Vision AI"""
    try:
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        job_id = str(uuid.uuid4())
        result = await generate_cad_from_image(str(file_path))
        
        if result.get("status") == "failed":
            return {
                "status": "error",
                "job_id": job_id,
                "error": result.get("error", "Unknown error")
            }
        
        return {
            "status": "completed",
            "job_id": job_id,
            "sketch_uploaded": file.filename,
            "cad_specification": result.get("cad_description"),
            "model_format": result.get("model_format", "STEP")
        }
    except Exception as e:
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
    return {
        "job_id": job_id,
        "status": "processing",
        "progress": 50
    }


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
    return {"jobs": []}


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
