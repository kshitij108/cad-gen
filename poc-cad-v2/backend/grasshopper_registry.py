"""
Grasshopper Template Registry and Management
Manages parametric CAD templates for different shapes
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum

# Template definitions directory
TEMPLATES_DIR = Path("./grasshopper_templates")
TEMPLATES_DIR.mkdir(exist_ok=True)


class TemplateShape(str, Enum):
    """Available parametric template shapes"""
    CUBE = "cube"
    SPHERE = "sphere"
    CYLINDER = "cylinder"
    CONE = "cone"
    WEDGE = "wedge"
    TORUS = "torus"


class GrasshopperTemplate:
    """Represents a Grasshopper parametric template"""
    
    def __init__(
        self,
        template_id: str,
        shape: TemplateShape,
        description: str,
        definition_path: str,
        input_parameters: Dict[str, str]
    ):
        self.template_id = template_id
        self.shape = shape
        self.description = description
        self.definition_path = definition_path
        self.input_parameters = input_parameters  # Maps CAD param names to GH input names
    
    def to_dict(self) -> dict:
        return {
            "template_id": self.template_id,
            "shape": self.shape,
            "description": self.description,
            "definition_path": self.definition_path,
            "input_parameters": self.input_parameters
        }


class TemplateRegistry:
    """Registry of available Grasshopper templates"""
    
    # Default templates - can be extended
    DEFAULT_TEMPLATES = {
        TemplateShape.CUBE: {
            "template_id": "template_cube_v1",
            "shape": TemplateShape.CUBE,
            "description": "Parametric cube with customizable dimensions and finish",
            "definition_path": "/grasshopper_templates/cube_parametric.gh",
            "input_parameters": {
                "length": "Length",
                "width": "Width",
                "height": "Height",
                "fillet_radius": "FilletRadius",
                "material": "Material",
                "finish": "Finish",
                "color": "Color"
            }
        },
        TemplateShape.SPHERE: {
            "template_id": "template_sphere_v1",
            "shape": TemplateShape.SPHERE,
            "description": "Parametric sphere with customizable radius",
            "definition_path": "/grasshopper_templates/sphere_parametric.gh",
            "input_parameters": {
                "radius": "Radius",
                "material": "Material",
                "finish": "Finish",
                "color": "Color"
            }
        },
        TemplateShape.CYLINDER: {
            "template_id": "template_cylinder_v1",
            "shape": TemplateShape.CYLINDER,
            "description": "Parametric cylinder with radius and height",
            "definition_path": "/grasshopper_templates/cylinder_parametric.gh",
            "input_parameters": {
                "radius": "Radius",
                "height": "Height",
                "fillet_radius": "FilletRadius",
                "material": "Material",
                "finish": "Finish",
                "color": "Color"
            }
        },
        TemplateShape.CONE: {
            "template_id": "template_cone_v1",
            "shape": TemplateShape.CONE,
            "description": "Parametric cone with base radius and height",
            "definition_path": "/grasshopper_templates/cone_parametric.gh",
            "input_parameters": {
                "radius": "BaseRadius",
                "height": "Height",
                "material": "Material",
                "finish": "Finish",
                "color": "Color"
            }
        },
        TemplateShape.TORUS: {
            "template_id": "template_torus_v1",
            "shape": TemplateShape.TORUS,
            "description": "Parametric torus with major and minor radius",
            "definition_path": "/grasshopper_templates/torus_parametric.gh",
            "input_parameters": {
                "major_radius": "MajorRadius",
                "minor_radius": "MinorRadius",
                "material": "Material",
                "finish": "Finish",
                "color": "Color"
            }
        },
        TemplateShape.WEDGE: {
            "template_id": "template_wedge_v1",
            "shape": TemplateShape.WEDGE,
            "description": "Parametric wedge with customizable dimensions",
            "definition_path": "/grasshopper_templates/wedge_parametric.gh",
            "input_parameters": {
                "length": "Length",
                "width": "Width",
                "height": "Height",
                "material": "Material",
                "finish": "Finish",
                "color": "Color"
            }
        }
    }
    
    def __init__(self):
        self.templates: Dict[str, GrasshopperTemplate] = {}
        self._load_default_templates()
        self._load_custom_templates()
    
    def _load_default_templates(self):
        """Load built-in default templates"""
        for shape, template_def in self.DEFAULT_TEMPLATES.items():
            template = GrasshopperTemplate(**template_def)
            self.templates[template.template_id] = template
    
    def _load_custom_templates(self):
        """Load custom templates from templates directory"""
        registry_file = TEMPLATES_DIR / "registry.json"
        if registry_file.exists():
            try:
                with open(registry_file, 'r') as f:
                    custom_templates = json.load(f)
                    for template_def in custom_templates:
                        template = GrassiopperTemplate(**template_def)
                        self.templates[template.template_id] = template
            except Exception as e:
                print(f"Error loading custom templates: {e}")
    
    def get_template(self, template_id: str) -> Optional[GrasshopperTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)
    
    def get_template_for_shape(self, shape: TemplateShape) -> Optional[GrasshopperTemplate]:
        """Get default template for a shape"""
        for template in self.templates.values():
            if template.shape == shape:
                return template
        return None
    
    def list_templates(self) -> List[dict]:
        """List all available templates"""
        return [t.to_dict() for t in self.templates.values()]
    
    def list_templates_by_shape(self, shape: TemplateShape) -> List[dict]:
        """List templates for a specific shape"""
        return [t.to_dict() for t in self.templates.values() if t.shape == shape]
    
    def register_custom_template(self, template_def: dict) -> bool:
        """Register a custom template"""
        try:
            template = GrassopperTemplate(**template_def)
            self.templates[template.template_id] = template
            
            # Persist to registry file
            registry_file = TEMPLATES_DIR / "registry.json"
            existing = []
            if registry_file.exists():
                with open(registry_file, 'r') as f:
                    existing = json.load(f)
            
            existing.append(template_def)
            with open(registry_file, 'w') as f:
                json.dump(existing, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error registering template: {e}")
            return False
    
    def map_cad_to_grasshopper(
        self,
        cad_params: dict,
        template: GrassopperTemplate
    ) -> dict:
        """
        Map CAD extraction parameters to Grasshopper input names
        
        Args:
            cad_params: Extracted CAD parameters from Gemini
            template: Target Grasshopper template
            
        Returns:
            Dictionary with Grasshopper input names and values
        """
        grasshopper_inputs = {}
        
        # Extract measurements
        measurements = cad_params.get("measurements", {})
        style = cad_params.get("style", {})
        parameters = cad_params.get("parameters", {})
        
        # Map measurements to template inputs
        for cad_key, gh_key in template.input_parameters.items():
            if cad_key in measurements:
                grasshopper_inputs[gh_key] = measurements[cad_key]
            elif cad_key in parameters:
                grasshopper_inputs[gh_key] = parameters[cad_key]
        
        # Add style parameters
        if "Material" in template.input_parameters.values():
            grasshopper_inputs["Material"] = style.get("material", "plastic")
        if "Finish" in template.input_parameters.values():
            grasshopper_inputs["Finish"] = style.get("finish", "smooth")
        if "Color" in template.input_parameters.values():
            grasshopper_inputs["Color"] = style.get("color", "#FFFFFF")
        
        return grasshopper_inputs


# Global registry instance
_registry = None


def get_template_registry() -> TemplateRegistry:
    """Get or create global template registry"""
    global _registry
    if _registry is None:
        _registry = TemplateRegistry()
    return _registry
