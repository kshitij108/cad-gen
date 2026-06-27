"""
Model Refinement System
Allows users to modify extracted parameters and regenerate STL
"""

import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
from enum import Enum

from cad_pipeline import get_cad_pipeline
from job_tracker import JobTracker


class RefinementAction(str, Enum):
    """Types of refinements users can make"""
    UPDATE_MEASUREMENTS = "update_measurements"
    UPDATE_STYLE = "update_style"
    UPDATE_PARAMETERS = "update_parameters"
    CHANGE_SHAPE = "change_shape"
    FULL_UPDATE = "full_update"


class ModelVersion:
    """Represents a version of a generated model"""
    
    def __init__(self, version_id: str, job_id: str, cad_params: dict, quality_score: float):
        self.version_id = version_id
        self.job_id = job_id
        self.cad_params = cad_params
        self.quality_score = quality_score
        self.created_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> dict:
        return {
            "version_id": self.version_id,
            "job_id": self.job_id,
            "cad_params": self.cad_params,
            "quality_score": self.quality_score,
            "created_at": self.created_at
        }


class ModelRefiner:
    """Handles model parameter refinement and regeneration"""
    
    def __init__(self, output_dir: Path = Path("./cad_models")):
        self.output_dir = output_dir
        self.pipeline = get_cad_pipeline()
    
    async def refine_model(
        self,
        original_job_id: str,
        updated_params: dict,
        refinement_type: RefinementAction,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Refine a model with updated parameters
        
        Args:
            original_job_id: ID of original generated model
            updated_params: Updated CAD parameters
            refinement_type: Type of refinement made
            user_id: Optional user ID for tracking
            
        Returns:
            Dictionary with new job details and version info
        """
        try:
            # Get original job details
            original_job_dir = self.output_dir / original_job_id
            original_extraction_file = original_job_dir / "extraction_params.json"
            
            if not original_extraction_file.exists():
                return {
                    "status": "error",
                    "error": "Original model not found"
                }
            
            # Load original parameters
            with open(original_extraction_file) as f:
                original_params = json.load(f)
            
            # Merge updated parameters
            refined_params = self._merge_parameters(original_params, updated_params, refinement_type)
            
            # Create new job for refined version
            import uuid
            new_job_id = str(uuid.uuid4())
            new_job_dir = self.output_dir / new_job_id
            new_job_dir.mkdir(exist_ok=True)
            
            # Create version metadata
            version_file = original_job_dir / "versions.json"
            versions = []
            if version_file.exists():
                with open(version_file) as f:
                    versions = json.load(f)
            
            # Generate with refined parameters (create as synthetic prompt)
            prompt = self._params_to_prompt(refined_params)
            
            # Run pipeline with refined parameters
            pipeline_result = await self.pipeline.generate_from_prompt(prompt, new_job_id, user_id)
            
            if pipeline_result["status"] != "success":
                return {
                    "status": "error",
                    "error": pipeline_result.get("error", "Refinement failed")
                }
            
            # Save refinement metadata
            refinement_metadata = {
                "version_id": new_job_id,
                "original_job_id": original_job_id,
                "refinement_type": refinement_type,
                "parameters_changed": self._get_parameter_diff(original_params, refined_params),
                "quality_improvement": pipeline_result.get("quality_score", 0) - 
                                     self._get_original_quality(original_job_dir),
                "created_at": datetime.utcnow().isoformat()
            }
            
            refinement_file = new_job_dir / "refinement_metadata.json"
            refinement_file.write_text(json.dumps(refinement_metadata, indent=2))
            
            # Update versions list
            versions.append({
                "version_id": new_job_id,
                "quality_score": pipeline_result.get("quality_score", 0),
                "refinement_type": refinement_type,
                "created_at": refinement_metadata["created_at"]
            })
            
            with open(version_file, 'w') as f:
                json.dump(versions, f, indent=2)
            
            return {
                "status": "success",
                "original_job_id": original_job_id,
                "refined_job_id": new_job_id,
                "refinement_type": refinement_type,
                "quality_improvement": refinement_metadata["quality_improvement"],
                "new_quality_score": pipeline_result.get("quality_score", 0),
                "parameters_changed": refinement_metadata["parameters_changed"],
                "file_url": f"/cad/download/{new_job_id}"
            }
        
        except Exception as e:
            print(f"Error in refine_model: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _merge_parameters(self, original: dict, updates: dict, action_type: RefinementAction) -> dict:
        """Merge original and updated parameters"""
        merged = json.loads(json.dumps(original))  # Deep copy
        
        if action_type == RefinementAction.UPDATE_MEASUREMENTS:
            if "measurements" in updates:
                merged["measurements"].update(updates["measurements"])
        
        elif action_type == RefinementAction.UPDATE_STYLE:
            if "style" in updates:
                merged["style"].update(updates["style"])
        
        elif action_type == RefinementAction.UPDATE_PARAMETERS:
            if "parameters" in updates:
                merged["parameters"].update(updates["parameters"])
        
        elif action_type == RefinementAction.CHANGE_SHAPE:
            if "shapes" in updates:
                merged["shapes"] = updates["shapes"]
        
        elif action_type == RefinementAction.FULL_UPDATE:
            merged = updates
        
        return merged
    
    def _get_parameter_diff(self, original: dict, updated: dict) -> Dict:
        """Calculate what parameters changed"""
        diff = {}
        
        for key in ["measurements", "shapes", "style", "parameters"]:
            if original.get(key) != updated.get(key):
                diff[key] = {
                    "before": original.get(key),
                    "after": updated.get(key)
                }
        
        return diff
    
    def _get_original_quality(self, job_dir: Path) -> float:
        """Get quality score of original model"""
        validation_file = job_dir / "stl_validation.json"
        if validation_file.exists():
            with open(validation_file) as f:
                data = json.load(f)
                return data.get("quality_score", 0)
        return 0
    
    def _params_to_prompt(self, params: dict) -> str:
        """Convert CAD parameters back to natural language prompt"""
        measurements = params.get("measurements", {})
        shapes = params.get("shapes", ["cube"])[0]
        style = params.get("style", {})
        
        prompt = f"A {measurements.get('length', 100)}{measurements.get('unit', 'mm')} "
        
        color = style.get("color", "default").replace("#", "")
        if len(color) > 3:
            color = "colored"
        prompt += f"{color} "
        
        material = style.get("material", "plastic")
        prompt += f"{material} "
        
        prompt += f"{shapes} "
        
        finish = style.get("finish", "smooth")
        if finish != "smooth":
            prompt += f"with {finish} finish"
        
        return prompt
    
    def get_model_history(self, job_id: str) -> Dict:
        """Get all versions/refinements of a model"""
        try:
            job_dir = self.output_dir / job_id
            version_file = job_dir / "versions.json"
            
            if not version_file.exists():
                return {
                    "job_id": job_id,
                    "versions": [],
                    "total_versions": 0
                }
            
            with open(version_file) as f:
                versions = json.load(f)
            
            return {
                "job_id": job_id,
                "versions": versions,
                "total_versions": len(versions),
                "current_quality": versions[-1]["quality_score"] if versions else 0
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def compare_versions(self, job_id1: str, job_id2: str) -> Dict:
        """Compare two model versions"""
        try:
            dir1 = self.output_dir / job_id1
            dir2 = self.output_dir / job_id2
            
            # Load validation results
            val1_file = dir1 / "stl_validation.json"
            val2_file = dir2 / "stl_validation.json"
            
            val1 = json.loads(val1_file.read_text()) if val1_file.exists() else {}
            val2 = json.loads(val2_file.read_text()) if val2_file.exists() else {}
            
            # Load CAD params
            param1_file = dir1 / "extraction_params.json"
            param2_file = dir2 / "extraction_params.json"
            
            param1 = json.loads(param1_file.read_text()) if param1_file.exists() else {}
            param2 = json.loads(param2_file.read_text()) if param2_file.exists() else {}
            
            return {
                "comparison": {
                    "model_1": {
                        "job_id": job_id1,
                        "quality_score": val1.get("quality_score", 0),
                        "triangle_count": val1.get("triangle_count", 0),
                        "file_size_mb": val1.get("file_size_mb", 0),
                        "shape": param1.get("shapes", ["unknown"])[0]
                    },
                    "model_2": {
                        "job_id": job_id2,
                        "quality_score": val2.get("quality_score", 0),
                        "triangle_count": val2.get("triangle_count", 0),
                        "file_size_mb": val2.get("file_size_mb", 0),
                        "shape": param2.get("shapes", ["unknown"])[0]
                    },
                    "quality_delta": val2.get("quality_score", 0) - val1.get("quality_score", 0),
                    "size_delta_mb": val2.get("file_size_mb", 0) - val1.get("file_size_mb", 0),
                    "triangle_delta": val2.get("triangle_count", 0) - val1.get("triangle_count", 0)
                }
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


def get_model_refiner() -> ModelRefiner:
    """Get model refiner instance"""
    return ModelRefiner()
