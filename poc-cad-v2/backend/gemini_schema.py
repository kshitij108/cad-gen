"""
Gemini Vision to Rhino CAD - JSON Schema Definitions
Enforces strict schema validation for AI-generated CAD parameters
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class UnitType(str, Enum):
    """Supported measurement units"""
    MM = "mm"
    CM = "cm"
    INCH = "in"
    M = "m"


class ShapeType(str, Enum):
    """Supported CAD shapes"""
    CUBE = "cube"
    SPHERE = "sphere"
    CYLINDER = "cylinder"
    CONE = "cone"
    WEDGE = "wedge"
    TORUS = "torus"
    CUSTOM = "custom"


class FinishType(str, Enum):
    """Surface finish types"""
    SMOOTH = "smooth"
    ROUGH = "rough"
    TEXTURED = "textured"


class MeasurementsSchema(BaseModel):
    """Dimensional measurements for CAD model"""
    length: float = Field(..., gt=0, description="Length in specified unit")
    width: float = Field(..., gt=0, description="Width in specified unit")
    height: float = Field(..., gt=0, description="Height in specified unit")
    unit: UnitType = Field(default=UnitType.MM, description="Measurement unit")
    radius: Optional[float] = Field(None, ge=0, description="Radius for spheres/cylinders")
    diameter: Optional[float] = Field(None, gt=0, description="Diameter for circular shapes")


class StyleSchema(BaseModel):
    """Visual and material styling properties"""
    material: str = Field(default="plastic", description="Material type (e.g., plastic, metal, wood)")
    finish: FinishType = Field(default=FinishType.SMOOTH, description="Surface finish")
    color: Optional[str] = Field(None, description="Hex color code (e.g., #FF5733)")
    transparency: Optional[float] = Field(None, ge=0, le=100, description="Transparency percentage")


class ParametersSchema(BaseModel):
    """Additional parametric properties for Grasshopper"""
    wall_thickness: Optional[float] = Field(None, description="Wall thickness for hollow shapes")
    fillet_radius: Optional[float] = Field(None, description="Corner fillet radius")
    texture_pattern: Optional[str] = Field(None, description="Texture pattern name")
    custom_params: Optional[dict] = Field(default_factory=dict, description="Additional custom parameters")


class CADExtractionSchema(BaseModel):
    """Main schema for Gemini-generated CAD parameters"""
    measurements: MeasurementsSchema = Field(..., description="Dimensional specifications")
    shapes: List[ShapeType] = Field(..., description="Primary shapes to use")
    style: StyleSchema = Field(default_factory=StyleSchema, description="Visual styling")
    parameters: ParametersSchema = Field(default_factory=ParametersSchema, description="Additional parameters")
    description: str = Field(..., description="Human-readable description of the model")
    confidence: Optional[float] = Field(default=0.85, ge=0, le=1, description="AI confidence in the extraction")


class PromptExtractionSchema(BaseModel):
    """Schema for text prompt analysis"""
    intent: str = Field(..., description="User's intent")
    complexity: str = Field(default="simple", description="Complexity level: simple, moderate, complex")
    features: List[str] = Field(default_factory=list, description="Identified features")
    extracted_cad: CADExtractionSchema = Field(..., description="Extracted CAD parameters")


class GeminiResponseWrapper(BaseModel):
    """Wrapper for raw Gemini response"""
    raw_response: str = Field(..., description="Raw text response from Gemini")
    extracted_cad: Optional[CADExtractionSchema] = Field(None, description="Parsed CAD schema")
    extraction_success: bool = Field(default=False, description="Whether extraction was successful")
    error_message: Optional[str] = Field(None, description="Error details if extraction failed")
