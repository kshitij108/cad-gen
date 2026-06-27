"""
Rhino Compute Client
REST API integration with Rhino Compute for parametric CAD generation
Supports both real Rhino Compute and mock mode for testing
"""

import os
import json
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pathlib import Path
from gemini_schema import CADExtractionSchema

load_dotenv()


class RhinoComputeClient:
    """Client for Rhino Compute REST API"""
    
    def __init__(self, use_mock: bool = False):
        """
        Initialize Rhino Compute client
        
        Args:
            use_mock: If True, use mock Grasshopper engine instead of real Rhino
        """
        self.use_mock = use_mock or os.getenv("USE_MOCK_GRASSHOPPER", "false").lower() == "true"
        self.base_url = os.getenv("RHINO_COMPUTE_URL", "http://localhost:8081")
        self.api_key = os.getenv("RHINO_COMPUTE_API_KEY")
        self.timeout = 60
        
        # Initialize mock engine if needed
        if self.use_mock:
            try:
                from mock_grasshopper_engine import MockGrasshopper, TemplateShape
                self.mock_engine = MockGrasshopper()
            except ImportError:
                print("Warning: mock_grasshopper_engine not available, falling back to real Rhino")
                self.use_mock = False
        
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Rhino Compute
        
        Args:
            method: HTTP method (GET, POST, etc)
            endpoint: API endpoint path
            data: Request payload
            headers: Custom headers
            
        Returns:
            Response JSON
        """
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            
            req_headers = {
                "Content-Type": "application/json",
                **(headers or {})
            }
            
            if self.api_key:
                req_headers["Authorization"] = f"Bearer {self.api_key}"
            
            response = requests.request(
                method=method,
                url=url,
                json=data,
                headers=req_headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status": "failed",
                "url": url if 'url' in locals() else None
            }
    
    def get_health(self) -> Dict[str, Any]:
        """Check Rhino Compute health"""
        return self._make_request("GET", "/health")
    
    def evaluate_grasshopper(
        self,
        definition_id: str,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate a Grasshopper definition with parametric inputs
        
        Args:
            definition_id: ID or name of the Grasshopper definition
            inputs: Dictionary of input parameters matching the definition
            
        Returns:
            Response with generated geometry/STL
        """
        if self.use_mock:
            return self._evaluate_grasshopper_mock(definition_id, inputs)
        
        payload = {
            "definition_id": definition_id,
            "parameters": inputs
        }
        
        return self._make_request("POST", "/grasshopper/evaluate", data=payload)
    
    def _evaluate_grasshopper_mock(
        self,
        definition_id: str,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock Grasshopper evaluation using mock engine"""
        try:
            from mock_grasshopper_engine import TemplateShape
            
            # Map definition_id to shape
            shape_map = {
                "cube": TemplateShape.CUBE,
                "sphere": TemplateShape.SPHERE,
                "cylinder": TemplateShape.CYLINDER,
                "cone": TemplateShape.CONE,
                "torus": TemplateShape.TORUS,
                "wedge": TemplateShape.WEDGE,
            }
            
            shape = shape_map.get(definition_id.lower(), TemplateShape.CUBE)
            
            # Create output file
            output_dir = Path("backend/cad_models/temp")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            import uuid
            job_id = str(uuid.uuid4())
            output_file = output_dir / f"{job_id}_{shape.value}.stl"
            
            # Generate STL
            metadata = self.mock_engine.generate_to_stl(shape, inputs, str(output_file))
            
            return {
                "status": "success",
                "job_id": job_id,
                "file_path": str(output_file),
                "metadata": metadata,
                "mode": "mock"
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "mode": "mock"
            }
    
    def generate_stl_from_cad_params(
        self,
        cad_params: CADExtractionSchema,
        definition_id: str = "default_parametric_model"
    ) -> Dict[str, Any]:
        """
        Generate STL from extracted CAD parameters
        
        Args:
            cad_params: Validated CAD extraction schema
            definition_id: Grasshopper template to use
            
        Returns:
            Response with STL file path or data
        """
        # Map CAD schema to Grasshopper inputs
        grasshopper_inputs = {
            "length": cad_params.measurements.length,
            "width": cad_params.measurements.width,
            "height": cad_params.measurements.height,
            "shape": cad_params.shapes[0] if cad_params.shapes else "cube",
            "material": cad_params.style.material,
            "finish": cad_params.style.finish,
            "color": cad_params.style.color,
            "wall_thickness": cad_params.parameters.wall_thickness,
            "fillet_radius": cad_params.parameters.fillet_radius,
        }
        
        return self.evaluate_grasshopper(definition_id, grasshopper_inputs)
    
    def get_available_definitions(self) -> Dict[str, Any]:
        """Get list of available Grasshopper definitions"""
        return self._make_request("GET", "/grasshopper/definitions")
    
    def upload_definition(
        self,
        definition_path: str,
        definition_name: str
    ) -> Dict[str, Any]:
        """
        Upload a Grasshopper definition file
        
        Args:
            definition_path: Path to .gh file
            definition_name: Name to register definition as
            
        Returns:
            Response with registration details
        """
        try:
            with open(definition_path, 'rb') as f:
                files = {'file': (definition_name, f, 'application/octet-stream')}
                
                url = f"{self.base_url}/grasshopper/definitions"
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                response = requests.post(
                    url,
                    files=files,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def get_stl_file(
        self,
        job_id: str,
        output_path: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Retrieve generated STL file
        
        Args:
            job_id: ID of completed CAD generation job
            output_path: Path to save STL file to
            
        Returns:
            STL file bytes or None if failed
        """
        try:
            url = f"{self.base_url}/jobs/{job_id}/output.stl"
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
            
            return response.content
        except Exception as e:
            print(f"Error retrieving STL file: {e}")
            return None


def get_rhino_client(use_mock: bool = False) -> RhinoComputeClient:
    """
    Factory function to get Rhino Compute client
    
    Args:
        use_mock: If True, use mock Grasshopper engine for testing
        
    Returns:
        RhinoComputeClient instance
    """
    return RhinoComputeClient(use_mock=use_mock)
