"""
AI Service Refactored for Gemini Vision
Deterministic JSON extraction for Grasshopper parametric templates
"""

import os
import json
import base64
from pathlib import Path
from typing import Optional
import google.generativeai as genai
from PIL import Image
import io
from dotenv import load_dotenv
from gemini_schema import CADExtractionSchema, PromptExtractionSchema, GeminiResponseWrapper

# Load environment variables
load_dotenv()


def get_gemini_client():
    """Initialize Gemini client with API key from environment"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    genai.configure(api_key=api_key)
    return genai


def _extract_json_from_response(response_text: str) -> dict:
    """
    Safely extract JSON from Gemini response.
    Handles cases where JSON is wrapped in markdown code blocks.
    """
    try:
        # Try direct JSON parsing
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Try extracting JSON from markdown code blocks
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end > start:
                return json.loads(response_text[start:end].strip())
        
        if "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            if end > start:
                return json.loads(response_text[start:end].strip())
        
        # If all else fails, raise error
        raise ValueError("Could not extract valid JSON from Gemini response")


async def generate_cad_from_image(file_path: str) -> dict:
    """
    Generate CAD parameters from an image using Gemini Vision.
    
    Args:
        file_path: Path to the uploaded image file
        
    Returns:
        dict with extracted CAD parameters, JSON schema, and status
    """
    try:
        # Validate file exists
        image_path = Path(file_path)
        if not image_path.exists():
            return {
                "error": "File not found",
                "status": "failed",
                "extraction_success": False
            }
        
        # Validate it's an image
        try:
            img = Image.open(image_path)
            img.verify()
            img = Image.open(image_path)  # Reopen after verify
        except Exception as e:
            return {
                "error": f"Invalid image file: {str(e)}",
                "status": "failed",
                "extraction_success": False
            }
        
        # Initialize Gemini
        get_gemini_client()
        model = genai.GenerativeModel("gemini-1.5-pro")
        
        # Read image file
        image_data = image_path.read_bytes()
        
        # Prepare extraction prompt with JSON schema guidance
        extraction_prompt = """Analyze this image and extract CAD modeling parameters in valid JSON format.

Return ONLY a valid JSON object (no markdown, no extra text) matching this structure:
{
  "measurements": {
    "length": number,
    "width": number,
    "height": number,
    "unit": "mm|cm|in|m",
    "radius": number or null,
    "diameter": number or null
  },
  "shapes": ["cube", "sphere", "cylinder", "cone", "wedge", "torus"],
  "style": {
    "material": "string",
    "finish": "smooth|rough|textured",
    "color": "hex code or null",
    "transparency": number or null
  },
  "parameters": {
    "wall_thickness": number or null,
    "fillet_radius": number or null,
    "texture_pattern": "string or null",
    "custom_params": {}
  },
  "description": "brief description",
  "confidence": 0.85
}

Extract all visible measurements, identify primary shapes, infer material/style. If uncertain, set confidence lower."""
        
        # Call Gemini with vision
        response = model.generate_content([
            extraction_prompt,
            {
                "mime_type": "image/jpeg",
                "data": image_data
            }
        ])
        
        response_text = response.text
        
        # Parse JSON response
        cad_params = _extract_json_from_response(response_text)
        
        # Validate against schema
        try:
            validated_cad = CADExtractionSchema(**cad_params)
            return {
                "status": "completed",
                "extraction_success": True,
                "cad_params": validated_cad.dict(),
                "raw_response": response_text,
                "file_name": image_path.name,
                "model_used": "gemini-1.5-pro"
            }
        except Exception as validation_error:
            return {
                "status": "completed",
                "extraction_success": False,
                "error": f"Schema validation failed: {str(validation_error)}",
                "raw_response": response_text,
                "file_name": image_path.name
            }
        
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "extraction_success": False,
            "file_name": str(file_path)
        }


async def generate_cad_from_prompt(prompt: str) -> dict:
    """
    Generate CAD parameters from a text prompt using Gemini.
    
    Args:
        prompt: Text description of the desired CAD model
        
    Returns:
        dict with extracted CAD parameters and status
    """
    try:
        # Initialize Gemini
        get_gemini_client()
        model = genai.GenerativeModel("gemini-1.5-pro")
        
        # Prepare extraction prompt with JSON schema guidance
        extraction_prompt = f"""User request: {prompt}

Analyze this request and extract CAD modeling parameters in valid JSON format.

Return ONLY a valid JSON object (no markdown, no extra text) matching this structure:
{{
  "measurements": {{
    "length": number,
    "width": number,
    "height": number,
    "unit": "mm|cm|in|m",
    "radius": number or null,
    "diameter": number or null
  }},
  "shapes": ["cube", "sphere", "cylinder", "cone", "wedge", "torus"],
  "style": {{
    "material": "string",
    "finish": "smooth|rough|textured",
    "color": "hex code or null",
    "transparency": number or null
  }},
  "parameters": {{
    "wall_thickness": number or null,
    "fillet_radius": number or null,
    "texture_pattern": "string or null",
    "custom_params": {{}}
  }},
  "description": "brief description",
  "confidence": 0.85
}}

Extract specifications from the request. Use reasonable defaults for unspecified dimensions. Infer material and style from context."""
        
        # Call Gemini
        response = model.generate_content(extraction_prompt)
        response_text = response.text
        
        # Parse JSON response
        cad_params = _extract_json_from_response(response_text)
        
        # Validate against schema
        try:
            validated_cad = CADExtractionSchema(**cad_params)
            return {
                "status": "completed",
                "extraction_success": True,
                "cad_params": validated_cad.dict(),
                "raw_response": response_text,
                "model_used": "gemini-1.5-pro"
            }
        except Exception as validation_error:
            return {
                "status": "completed",
                "extraction_success": False,
                "error": f"Schema validation failed: {str(validation_error)}",
                "raw_response": response_text
            }
        
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "extraction_success": False
        }


async def extract_measurements_from_image(file_path: str) -> Optional[dict]:
    """
    Specialized function to extract only measurements from an image.
    
    Args:
        file_path: Path to image file
        
    Returns:
        dict with measurements or None if extraction failed
    """
    try:
        result = await generate_cad_from_image(file_path)
        if result.get("extraction_success"):
            return result.get("cad_params", {}).get("measurements")
        return None
    except Exception as e:
        print(f"Error extracting measurements: {e}")
        return None


async def extract_style_from_image(file_path: str) -> Optional[dict]:
    """
    Specialized function to extract only style from an image.
    
    Args:
        file_path: Path to image file
        
    Returns:
        dict with style or None if extraction failed
    """
    try:
        result = await generate_cad_from_image(file_path)
        if result.get("extraction_success"):
            return result.get("cad_params", {}).get("style")
        return None
    except Exception as e:
        print(f"Error extracting style: {e}")
        return None
