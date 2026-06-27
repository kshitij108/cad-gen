"""
CAD Generation Pipeline Orchestrator
Phase 2: Coordinates Gemini extraction → Rhino Compute → STL validation
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from enum import Enum

from cad_service import generate_cad_from_image, generate_cad_from_prompt
from rhino_client import get_rhino_client
from grasshopper_registry import get_template_registry, TemplateShape
from stl_validator import validate_stl_file
from job_tracker import JobTracker


class PipelineStage(str, Enum):
    """Pipeline execution stages"""
    INITIALIZING = "initializing"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    CONVERTING = "converting"
    GENERATING = "generating"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


class CADGenerationPipeline:
    """Orchestrates the complete CAD generation pipeline"""
    
    def __init__(self, output_dir: Path = Path("./cad_models")):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.rhino_client = get_rhino_client()
        self.template_registry = get_template_registry()
    
    async def generate_from_image(
        self,
        image_path: str,
        job_id: str,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Full pipeline: Image → Gemini extraction → Rhino CAD → STL validation
        
        Args:
            image_path: Path to reference image
            job_id: Unique job identifier
            user_id: Optional user ID for tracking
            
        Returns:
            Dictionary with generation results
        """
        try:
            job_dir = self.output_dir / job_id
            job_dir.mkdir(exist_ok=True)
            
            # Stage 1: Extract CAD parameters from image
            JobTracker.update_job(job_id, status="processing", progress=10, stage=PipelineStage.EXTRACTING.value)
            
            extraction_result = await generate_cad_from_image(image_path)
            
            if not extraction_result.get("extraction_success"):
                JobTracker.update_job(job_id, status="failed", stage=PipelineStage.FAILED.value)
                return {
                    "status": "error",
                    "job_id": job_id,
                    "error": extraction_result.get("error", "Image extraction failed"),
                    "stage": PipelineStage.EXTRACTING.value
                }
            
            cad_params = extraction_result.get("cad_params")
            confidence = cad_params.get("confidence", 0.85)
            
            # Save extraction parameters
            extraction_file = job_dir / "extraction_params.json"
            extraction_file.write_text(json.dumps(cad_params, indent=2))
            
            JobTracker.update_job(
                job_id,
                progress=25,
                stage=PipelineStage.VALIDATING.value,
                cad_specification=json.dumps(cad_params)[:500]
            )
            
            # Stage 2: Validate extracted parameters
            validation_errors = self._validate_cad_params(cad_params)
            if validation_errors:
                JobTracker.update_job(job_id, status="failed", stage=PipelineStage.FAILED.value)
                return {
                    "status": "error",
                    "job_id": job_id,
                    "error": f"Validation failed: {', '.join(validation_errors)}",
                    "stage": PipelineStage.VALIDATING.value
                }
            
            # Stage 3: Select appropriate template
            JobTracker.update_job(job_id, progress=40, stage=PipelineStage.CONVERTING.value)
            
            shape = cad_params.get("shapes", ["cube"])[0]
            try:
                template_shape = TemplateShape[shape.upper()]
            except KeyError:
                template_shape = TemplateShape.CUBE
            
            template = self.template_registry.get_template_for_shape(template_shape)
            if not template:
                JobTracker.update_job(job_id, status="failed", stage=PipelineStage.FAILED.value)
                return {
                    "status": "error",
                    "job_id": job_id,
                    "error": f"No template found for shape: {shape}",
                    "stage": PipelineStage.CONVERTING.value
                }
            
            # Map CAD params to Grasshopper inputs
            grasshopper_inputs = self.template_registry.map_cad_to_grasshopper(cad_params, template)
            
            conversion_file = job_dir / "grasshopper_inputs.json"
            conversion_file.write_text(json.dumps(grasshopper_inputs, indent=2))
            
            # Stage 4: Generate STL via Rhino Compute
            JobTracker.update_job(job_id, progress=60, stage=PipelineStage.GENERATING.value)
            
            rhino_result = self.rhino_client.generate_stl_from_cad_params(
                cad_params=cad_params,
                definition_id=template.template_id
            )
            
            if rhino_result.get("error"):
                JobTracker.update_job(job_id, status="failed", stage=PipelineStage.FAILED.value)
                return {
                    "status": "error",
                    "job_id": job_id,
                    "error": f"Rhino Compute error: {rhino_result.get('error')}",
                    "stage": PipelineStage.GENERATING.value
                }
            
            # Download STL file from Rhino
            stl_path = job_dir / "model.stl"
            stl_bytes = self.rhino_client.get_stl_file(rhino_result.get("job_id"), str(stl_path))
            
            if not stl_path.exists():
                JobTracker.update_job(job_id, status="failed", stage=PipelineStage.FAILED.value)
                return {
                    "status": "error",
                    "job_id": job_id,
                    "error": "Failed to retrieve STL file from Rhino Compute",
                    "stage": PipelineStage.GENERATING.value
                }
            
            # Stage 5: Validate generated STL
            JobTracker.update_job(job_id, progress=80, stage=PipelineStage.FINALIZING.value)
            
            stl_validation = validate_stl_file(str(stl_path))
            
            if not stl_validation["is_valid"]:
                JobTracker.update_job(job_id, status="failed", stage=PipelineStage.FAILED.value)
                return {
                    "status": "error",
                    "job_id": job_id,
                    "error": f"STL validation failed: {', '.join(stl_validation['issues'])}",
                    "stage": PipelineStage.FINALIZING.value,
                    "validation": stl_validation
                }
            
            # Save validation results
            validation_file = job_dir / "stl_validation.json"
            validation_file.write_text(json.dumps(stl_validation, indent=2))
            
            # Complete
            JobTracker.update_job(
                job_id,
                status="completed",
                progress=100,
                stage=PipelineStage.COMPLETED.value,
                file_path=str(stl_path),
                file_format="STL"
            )
            
            return {
                "status": "success",
                "job_id": job_id,
                "file_path": str(stl_path),
                "file_url": f"/cad/download/{job_id}",
                "cad_parameters": cad_params,
                "template": {
                    "id": template.template_id,
                    "shape": template.shape,
                    "description": template.description
                },
                "stl_validation": stl_validation,
                "quality_score": stl_validation["quality_score"],
                "model_format": "STL",
                "generation_confidence": confidence
            }
        
        except Exception as e:
            print(f"Pipeline error: {e}")
            import traceback
            traceback.print_exc()
            JobTracker.update_job(job_id, status="failed", stage=PipelineStage.FAILED.value)
            return {
                "status": "error",
                "job_id": job_id,
                "error": str(e),
                "stage": PipelineStage.FAILED.value
            }
    
    async def generate_from_prompt(
        self,
        prompt: str,
        job_id: str,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Full pipeline: Text prompt → Gemini extraction → Rhino CAD → STL validation
        
        Args:
            prompt: Text description of desired model
            job_id: Unique job identifier
            user_id: Optional user ID for tracking
            
        Returns:
            Dictionary with generation results
        """
        try:
            job_dir = self.output_dir / job_id
            job_dir.mkdir(exist_ok=True)
            
            # Stage 1: Extract CAD parameters from prompt
            JobTracker.update_job(job_id, status="processing", progress=10, stage=PipelineStage.EXTRACTING.value)
            
            extraction_result = await generate_cad_from_prompt(prompt)
            
            if not extraction_result.get("extraction_success"):
                JobTracker.update_job(job_id, status="failed", stage=PipelineStage.FAILED.value)
                return {
                    "status": "error",
                    "job_id": job_id,
                    "error": extraction_result.get("error", "Prompt extraction failed"),
                    "stage": PipelineStage.EXTRACTING.value
                }
            
            cad_params = extraction_result.get("cad_params")
            confidence = cad_params.get("confidence", 0.85)
            
            # Save extraction parameters
            extraction_file = job_dir / "extraction_params.json"
            extraction_file.write_text(json.dumps(cad_params, indent=2))
            
            JobTracker.update_job(
                job_id,
                progress=25,
                stage=PipelineStage.VALIDATING.value,
                cad_specification=json.dumps(cad_params)[:500]
            )
            
            # Stage 2: Validate extracted parameters
            validation_errors = self._validate_cad_params(cad_params)
            if validation_errors:
                JobTracker.update_job(job_id, status="failed", stage=PipelineStage.FAILED.value)
                return {
                    "status": "error",
                    "job_id": job_id,
                    "error": f"Validation failed: {', '.join(validation_errors)}",
                    "stage": PipelineStage.VALIDATING.value
                }
            
            # Stage 3: Select appropriate template
            JobTracker.update_job(job_id, progress=40, stage=PipelineStage.CONVERTING.value)
            
            shape = cad_params.get("shapes", ["cube"])[0]
            try:
                template_shape = TemplateShape[shape.upper()]
            except KeyError:
                template_shape = TemplateShape.CUBE
            
            template = self.template_registry.get_template_for_shape(template_shape)
            if not template:
                JobTracker.update_job(job_id, status="failed", stage=PipelineStage.FAILED.value)
                return {
                    "status": "error",
                    "job_id": job_id,
                    "error": f"No template found for shape: {shape}",
                    "stage": PipelineStage.CONVERTING.value
                }
            
            # Map CAD params to Grasshopper inputs
            grasshopper_inputs = self.template_registry.map_cad_to_grasshopper(cad_params, template)
            
            conversion_file = job_dir / "grasshopper_inputs.json"
            conversion_file.write_text(json.dumps(grasshopper_inputs, indent=2))
            
            # Stage 4: Generate STL via Rhino Compute
            JobTracker.update_job(job_id, progress=60, stage=PipelineStage.GENERATING.value)
            
            rhino_result = self.rhino_client.generate_stl_from_cad_params(
                cad_params=cad_params,
                definition_id=template.template_id
            )
            
            if rhino_result.get("error"):
                JobTracker.update_job(job_id, status="failed", stage=PipelineStage.FAILED.value)
                return {
                    "status": "error",
                    "job_id": job_id,
                    "error": f"Rhino Compute error: {rhino_result.get('error')}",
                    "stage": PipelineStage.GENERATING.value
                }
            
            # Download STL file from Rhino
            stl_path = job_dir / "model.stl"
            stl_bytes = self.rhino_client.get_stl_file(rhino_result.get("job_id"), str(stl_path))
            
            if not stl_path.exists():
                JobTracker.update_job(job_id, status="failed", stage=PipelineStage.FAILED.value)
                return {
                    "status": "error",
                    "job_id": job_id,
                    "error": "Failed to retrieve STL file from Rhino Compute",
                    "stage": PipelineStage.GENERATING.value
                }
            
            # Stage 5: Validate generated STL
            JobTracker.update_job(job_id, progress=80, stage=PipelineStage.FINALIZING.value)
            
            stl_validation = validate_stl_file(str(stl_path))
            
            if not stl_validation["is_valid"]:
                JobTracker.update_job(job_id, status="failed", stage=PipelineStage.FAILED.value)
                return {
                    "status": "error",
                    "job_id": job_id,
                    "error": f"STL validation failed: {', '.join(stl_validation['issues'])}",
                    "stage": PipelineStage.FINALIZING.value,
                    "validation": stl_validation
                }
            
            # Save validation results
            validation_file = job_dir / "stl_validation.json"
            validation_file.write_text(json.dumps(stl_validation, indent=2))
            
            # Complete
            JobTracker.update_job(
                job_id,
                status="completed",
                progress=100,
                stage=PipelineStage.COMPLETED.value,
                file_path=str(stl_path),
                file_format="STL"
            )
            
            return {
                "status": "success",
                "job_id": job_id,
                "file_path": str(stl_path),
                "file_url": f"/cad/download/{job_id}",
                "cad_parameters": cad_params,
                "template": {
                    "id": template.template_id,
                    "shape": template.shape,
                    "description": template.description
                },
                "stl_validation": stl_validation,
                "quality_score": stl_validation["quality_score"],
                "model_format": "STL",
                "generation_confidence": confidence
            }
        
        except Exception as e:
            print(f"Pipeline error: {e}")
            import traceback
            traceback.print_exc()
            JobTracker.update_job(job_id, status="failed", stage=PipelineStage.FAILED.value)
            return {
                "status": "error",
                "job_id": job_id,
                "error": str(e),
                "stage": PipelineStage.FAILED.value
            }
    
    def _validate_cad_params(self, cad_params: Dict) -> list:
        """
        Validate extracted CAD parameters
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required fields
        if not cad_params.get("measurements"):
            errors.append("Missing measurements")
        
        if not cad_params.get("shapes"):
            errors.append("Missing shapes")
        
        # Validate measurements
        measurements = cad_params.get("measurements", {})
        if measurements:
            for dim in ["length", "width", "height"]:
                val = measurements.get(dim)
                if val is not None:
                    if not isinstance(val, (int, float)) or val <= 0:
                        errors.append(f"Invalid {dim}: must be positive number")
        
        # Validate shapes
        shapes = cad_params.get("shapes", [])
        valid_shapes = {s.value for s in TemplateShape}
        for shape in shapes:
            if shape not in valid_shapes:
                errors.append(f"Invalid shape: {shape}")
        
        return errors


def get_cad_pipeline() -> CADGenerationPipeline:
    """Get CAD generation pipeline instance"""
    return CADGenerationPipeline()
