from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
from pathlib import Path
from dotenv import load_dotenv
from models import UserRegister, UserLogin, Token, PromptRequest, JobResponse
from cad_pipeline import get_cad_pipeline
from job_tracker import JobTracker
from auth_storage import AuthManager
from grasshopper_registry import get_template_registry
from stl_validator import validate_stl_file
from model_refiner import get_model_refiner, RefinementAction
from batch_processor import get_batch_processor, BatchProcessingMode
from export_manager import get_export_manager
import json
import uuid

load_dotenv()

app = FastAPI(
    title="CAD Generation API",
    description="AI-Assisted CAD Model Generation Platform - Gemini Vision + Rhino Compute + Batch Processing",
    version="3.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
UPLOAD_DIR = Path("./uploads")
OUTPUT_DIR = Path("./cad_models")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Initialize Phase 2 pipeline and Phase 3 components
cad_pipeline = get_cad_pipeline()
model_refiner = get_model_refiner()
batch_processor = get_batch_processor(cad_pipeline)
export_manager = get_export_manager()


# Routes
@app.get("/")
async def root():
    return {
        "message": "CAD Generation API v3.0",
        "architecture": "Gemini Vision + Rhino Compute + Batch Processing",
        "phases": {
            "phase_1": "Gemini Vision extraction & JSON schema validation",
            "phase_2": "Rhino Compute integration with STL validation",
            "phase_3": "Model refinement, batch processing, multi-format export"
        },
        "capabilities": ["image-to-cad", "prompt-to-cad", "model-refinement", "batch-generation", "format-conversion"]
    }


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
    """
    PHASE 2: Generate manufacturing-ready STL from text prompt
    
    Pipeline: Text Prompt → Gemini 1.5 Pro → JSON Parameters → Rhino Compute → STL
    
    Returns complete CAD model with validation
    """
    try:
        job_id = str(uuid.uuid4())
        
        # Create job tracker entry
        JobTracker.create_job(job_id, "prompt")
        
        # Run Phase 2 pipeline
        result = await cad_pipeline.generate_from_prompt(request.prompt, job_id)
        
        return result
        
    except Exception as e:
        print(f"Error in generate_from_prompt: {e}")
        import traceback
        traceback.print_exc()
        if 'job_id' in locals():
            JobTracker.update_job(job_id, status="failed")
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/cad/generate-from-image")
async def generate_from_image(file: UploadFile = File(...)):
    """
    PHASE 2: Generate manufacturing-ready STL from reference image
    
    Pipeline: Image → Gemini Vision → JSON Parameters → Rhino Compute → STL
    
    Returns complete CAD model with validation
    """
    try:
        job_id = str(uuid.uuid4())
        job_dir = OUTPUT_DIR / job_id
        job_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # Create job tracker entry
        JobTracker.create_job(job_id, "image")
        
        # Run Phase 2 pipeline
        result = await cad_pipeline.generate_from_image(str(file_path), job_id)
        
        return result
        
    except Exception as e:
        print(f"Error in generate_from_image: {e}")
        import traceback
        traceback.print_exc()
        if 'job_id' in locals():
            JobTracker.update_job(job_id, status="failed")
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/cad/generate-from-sketch")
async def generate_from_sketch(file: UploadFile = File(...)):
    """
    PHASE 2: Generate CAD from hand-drawn sketch
    
    Same pipeline as image: Sketch → Gemini Vision → JSON → Rhino → STL
    """
    try:
        job_id = str(uuid.uuid4())
        job_dir = OUTPUT_DIR / job_id
        job_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # Create job tracker entry
        JobTracker.create_job(job_id, "sketch")
        
        # Run Phase 2 pipeline
        result = await cad_pipeline.generate_from_image(str(file_path), job_id)
        
        return result
        
    except Exception as e:
        print(f"Error in generate_from_sketch: {e}")
        import traceback
        traceback.print_exc()
        if 'job_id' in locals():
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


# ============================================================================
# PHASE 2: New Endpoints for Gemini Vision + Rhino Compute Integration
# ============================================================================

@app.get("/cad/templates")
async def list_templates():
    """
    List available Grasshopper parametric templates
    
    Each template represents a shape that can be customized via JSON parameters
    """
    try:
        registry = get_template_registry()
        templates = registry.list_templates()
        return {
            "status": "success",
            "templates": templates,
            "total": len(templates)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/cad/templates/{shape}")
async def list_templates_by_shape(shape: str):
    """List templates for a specific shape (cube, sphere, cylinder, etc)"""
    try:
        registry = get_template_registry()
        from grasshopper_registry import TemplateShape
        
        shape_enum = TemplateShape[shape.upper()]
        templates = registry.list_templates_by_shape(shape_enum)
        
        return {
            "status": "success",
            "shape": shape,
            "templates": templates,
            "total": len(templates)
        }
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Unknown shape: {shape}")
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/cad/job/{job_id}")
async def get_job_status(job_id: str):
    """
    Get detailed status of a CAD generation job
    
    Includes extraction parameters, validation results, and generation progress
    """
    job = JobTracker.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    response = {
        "job_id": job_id,
        "status": job.get("status"),
        "progress": job.get("progress"),
        "stage": job.get("stage"),
        "job_type": job.get("job_type"),
        "cad_specification": job.get("cad_specification"),
        "file_path": job.get("file_path"),
        "file_format": job.get("file_format"),
        "created_at": job.get("created_at")
    }
    
    # Add download URL if file is available
    if job.get("file_path") and Path(job.get("file_path")).exists():
        response["file_url"] = f"/cad/download/{job_id}"
    
    # Add validation results if available
    job_dir = OUTPUT_DIR / job_id
    validation_file = job_dir / "stl_validation.json"
    if validation_file.exists():
        with open(validation_file) as f:
            response["stl_validation"] = json.load(f)
    
    # Add extraction parameters if available
    extraction_file = job_dir / "extraction_params.json"
    if extraction_file.exists():
        with open(extraction_file) as f:
            response["cad_parameters"] = json.load(f)
    
    return response


@app.get("/cad/download/{job_id}")
async def download_cad(job_id: str):
    """Download generated CAD file (STL format)"""
    job = JobTracker.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if not job.get("file_path") or not Path(job.get("file_path")).exists():
        raise HTTPException(status_code=404, detail="CAD file not available")
    
    file_path = job.get("file_path")
    file_ext = Path(file_path).suffix
    media_type = "model/stl"
    
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=f"model_{job_id}{file_ext}"
    )


@app.get("/cad/job/{job_id}/extraction")
async def get_extraction_parameters(job_id: str):
    """
    Get Gemini extracted CAD parameters for a job
    
    Returns measurements, shapes, style, and other parameters
    """
    job_dir = OUTPUT_DIR / job_id
    extraction_file = job_dir / "extraction_params.json"
    
    if not extraction_file.exists():
        raise HTTPException(status_code=404, detail="Extraction parameters not found")
    
    with open(extraction_file) as f:
        params = json.load(f)
    
    return {
        "job_id": job_id,
        "extracted_parameters": params
    }


@app.get("/cad/job/{job_id}/validation")
async def get_stl_validation(job_id: str):
    """
    Get STL validation results for a job
    
    Includes triangle count, file size, bounds checking, and quality score
    """
    job_dir = OUTPUT_DIR / job_id
    validation_file = job_dir / "stl_validation.json"
    
    if not validation_file.exists():
        raise HTTPException(status_code=404, detail="Validation results not found")
    
    with open(validation_file) as f:
        validation = json.load(f)
    
    return {
        "job_id": job_id,
        "validation": validation
    }


@app.get("/cad/job/{job_id}/grasshopper-inputs")
async def get_grasshopper_inputs(job_id: str):
    """
    Get the Grasshopper input mapping for a job
    
    Shows how Gemini extraction parameters were mapped to Rhino template inputs
    """
    job_dir = OUTPUT_DIR / job_id
    conversion_file = job_dir / "grasshopper_inputs.json"
    
    if not conversion_file.exists():
        raise HTTPException(status_code=404, detail="Grasshopper inputs not found")
    
    with open(conversion_file) as f:
        inputs = json.load(f)
    
    return {
        "job_id": job_id,
        "grasshopper_inputs": inputs
    }


@app.post("/cad/validate-extraction")
async def validate_extraction_manual(cad_params: dict):
    """
    Validate CAD extraction parameters without running full pipeline
    
    Useful for testing or parameter adjustment before generation
    """
    try:
        # Validate using pipeline's validation method
        validation_errors = cad_pipeline._validate_cad_params(cad_params)
        
        return {
            "is_valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "parameters": cad_params
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# ============================================================================
# PHASE 3: Model Refinement, Batch Processing, and Multi-Format Export
# ============================================================================

@app.post("/cad/refine/{job_id}")
async def refine_model(job_id: str, request: dict):
    """
    PHASE 3: Refine an existing model with updated parameters
    
    Allows users to modify extracted parameters and regenerate STL without re-analyzing
    
    Request body:
    {
        "refinement_type": "update_measurements",  # or update_style, update_parameters, etc
        "updated_params": {...}
    }
    """
    try:
        refinement_type = request.get("refinement_type", "full_update")
        updated_params = request.get("updated_params", {})
        
        result = await model_refiner.refine_model(
            job_id,
            updated_params,
            RefinementAction[refinement_type.upper()]
        )
        
        return result
    
    except Exception as e:
        print(f"Error in refine_model: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/cad/history/{job_id}")
async def get_model_history(job_id: str):
    """
    Get all refinement versions and history of a model
    
    Shows progression of refinements with quality scores
    """
    try:
        history = model_refiner.get_model_history(job_id)
        return history
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/cad/compare")
async def compare_models(job_id_1: str, job_id_2: str):
    """
    Compare two model versions side-by-side
    
    Shows differences in quality, size, complexity
    """
    try:
        comparison = model_refiner.compare_versions(job_id_1, job_id_2)
        return comparison
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/cad/batch/create")
async def create_batch(requests: list):
    """
    PHASE 3: Create a batch job for multiple CAD generations
    
    Request body:
    {
        "requests": [
            {"prompt": "100mm cube"},
            {"prompt": "50mm sphere"},
            {"image_path": "/uploads/ref.jpg"}
        ],
        "mode": "sequential",  # or parallel, throttled
        "max_concurrent": 3
    }
    """
    try:
        mode = BatchProcessingMode.SEQUENTIAL
        max_concurrent = 3
        
        result = await batch_processor.create_batch(
            requests,
            mode,
            max_concurrent
        )
        
        return result
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/cad/batch/{batch_id}/process")
async def process_batch(batch_id: str):
    """
    Start processing a batch job
    
    Processes all requests according to the batch's configured mode
    """
    try:
        result = await batch_processor.process_batch(batch_id)
        return result
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/cad/batch/{batch_id}/status")
async def get_batch_status(batch_id: str):
    """Get current status of a batch job"""
    try:
        status = batch_processor.get_batch_status(batch_id)
        return status
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/cad/batch/{batch_id}/results")
async def get_batch_results(batch_id: str, details: bool = False):
    """
    Get results of a completed batch
    
    Query parameter: details=true for detailed results
    """
    try:
        results = batch_processor.get_batch_results(batch_id, details)
        return results
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/cad/batch/{batch_id}/manifest")
async def get_batch_manifest(batch_id: str):
    """Get exportable manifest of batch for record-keeping"""
    try:
        manifest = batch_processor.export_batch_manifest(batch_id)
        return manifest
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/cad/export/formats")
async def get_export_formats():
    """
    Get list of supported export formats
    
    Returns format details, supported features, and suitability information
    """
    try:
        formats = export_manager.get_export_formats()
        return formats
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/cad/export/{job_id}")
async def export_model(job_id: str, format: str, quality: str = "normal"):
    """
    PHASE 3: Export generated model to alternative format
    
    Supported formats: stl_ascii, stl_binary, obj, step (requires Rhino), iges (requires Rhino)
    
    Query parameters:
        format: Target export format
        quality: For formats that support it (draft, normal, production)
    """
    try:
        result = await export_manager.export(job_id, format, quality)
        return result
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/cad/download/{job_id}/{format}")
async def download_exported_model(job_id: str, format: str):
    """
    Download model in specified format
    
    Example: GET /cad/download/abc123/obj
    """
    try:
        job_dir = OUTPUT_DIR / job_id
        filename = export_manager._get_output_filename(job_id, format)
        file_path = job_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Exported {format} file not found")
        
        media_types = {
            "stl_ascii": "model/stl",
            "stl_binary": "model/stl",
            "obj": "model/obj",
            "step": "model/step",
            "iges": "model/iges",
            "vrml": "model/vrml"
        }
        
        return FileResponse(
            file_path,
            media_type=media_types.get(format, "application/octet-stream"),
            filename=f"model_{job_id}{Path(filename).suffix}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# ============================================================================
# Legacy Endpoints - Maintained for backward compatibility
# ============================================================================

@app.get("/cad/job/{job_id}")
async def get_legacy_job_status(job_id: str):
    """Legacy endpoint - use /cad/job/{job_id} instead"""
    pass


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
