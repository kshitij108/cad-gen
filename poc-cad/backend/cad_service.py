import os
import base64
from pathlib import Path
from anthropic import Anthropic
from PIL import Image
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_anthropic_client():
    """Get Anthropic client with API key from environment"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
    return Anthropic(api_key=api_key)

async def generate_cad_from_image(file_path: str) -> dict:
    """
    Generate CAD model from an image using Claude Vision (Code-as-CAD pipeline)
    
    Args:
        file_path: Path to the uploaded image file
        
    Returns:
        dict with code (OpenSCAD), code_type, and status
    """
    try:
        # Read and process image
        image_path = Path(file_path)
        if not image_path.exists():
            return {"error": "File not found", "status": "failed"}
        
        # Try to verify it's a valid image
        try:
            img = Image.open(image_path)
            img.verify()
        except Exception as e:
            # If it's not a valid image, we'll still try to process it
            pass
        
        # Prepare image for Claude
        with open(file_path, "rb") as img_file:
            image_data = base64.standard_b64encode(img_file.read()).decode("utf-8")
        
        # Determine media type
        file_ext = image_path.suffix.lower()
        media_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        media_type = media_type_map.get(file_ext, "image/jpeg")
        
        # Call Claude with vision capability to generate CadQuery code
        client = get_anthropic_client()
        message = client.messages.create(
            model="claude-opus-4-1",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": """Generate ONLY executable Python/CadQuery code - no markdown, no ``` symbols.

from cadquery import Workplane
import cadquery as cq

result = Workplane("XY").box(10, 10, 10)  # or .sphere(5) or .cylinder(5, 10)

That's it. No explanations, no markdown code fences, just the raw Python code."""
                        }
                    ],
                }
            ],
        )
        
        cadquery_code = message.content[0].text
        
        return {
            "status": "completed",
            "code": cadquery_code,
            "code_type": "cadquery",
            "file_name": image_path.name
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "code": None
        }


async def generate_cad_from_prompt(prompt: str) -> dict:
    """
    Generate CAD model from text prompt using Claude (Code-as-CAD pipeline)
    
    Args:
        prompt: Text description of the desired CAD model
        
    Returns:
        dict with code (OpenSCAD), code_type, and status
    """
    try:
        client = get_anthropic_client()
        message = client.messages.create(
            model="claude-opus-4-1",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": f"""Generate ONLY executable Python code - no markdown, no ``` symbols.

Request: {prompt}

from cadquery import Workplane
import cadquery as cq

result = Workplane("XY").box(10, 10, 10)  # or .sphere() or .cylinder()

Raw code only, no explanations."""
                }
            ],
        )
        
        cadquery_code = message.content[0].text
        
        return {
            "status": "completed",
            "code": cadquery_code,
            "code_type": "cadquery"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "code": None
        }
