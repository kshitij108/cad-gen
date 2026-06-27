# Phase 1: AI Service Refactoring - Implementation Guide

## Overview
This document details Phase 1 of the Gemini-to-Rhino CAD architecture pivot. The system now uses Google Gemini Vision to extract deterministic JSON parameters from images/prompts, eliminating the non-deterministic code generation approach.

---

## What Changed

### Before (Claude-based)
- Claude Opus generates ad-hoc Python/CadQuery code
- Non-deterministic output format
- Difficult to validate and route to Rhino
- Coupled AI output to CadQuery execution

### After (Gemini-based)
- Gemini 1.5 Pro extracts structured JSON parameters
- Deterministic, schema-validated output
- Clean decoupling: AI → JSON → Grasshopper → STL
- Parameters flow directly to Rhino Compute

---

## Architecture Components

### 1. **Gemini Schema** (`gemini_schema.py`)
Pydantic models enforcing strict JSON structure:
- `MeasurementsSchema`: length, width, height, radius, diameter
- `ShapeType`: cube, sphere, cylinder, cone, wedge, torus
- `StyleSchema`: material, finish, color, transparency
- `CADExtractionSchema`: complete validated output

### 2. **AI Service** (`cad_service.py`)
Refactored to use `google-generativeai` SDK:
- `generate_cad_from_image()`: Analyzes images → extracts JSON
- `generate_cad_from_prompt()`: Analyzes text → extracts JSON
- Built-in JSON extraction and schema validation
- Returns deterministic, validated CAD parameters

### 3. **Rhino Client** (`rhino_client.py`)
REST API wrapper for Rhino Compute:
- `evaluate_grasshopper()`: Execute parametric templates
- `generate_stl_from_cad_params()`: Maps extracted JSON → Grasshopper inputs
- Health checks and error handling
- Support for definition uploads and job tracking

---

## Setup Instructions

### Step 1: Install Dependencies
```bash
cd /Users/kshitijbhatt/Desktop/sagar/poc-cad-v2/backend
pip install -r requirements.txt
```

**New dependencies added:**
- `google-generativeai>=0.5.0` - Gemini SDK
- `requests>=2.31.0` - HTTP client for Rhino Compute

### Step 2: Configure Environment Variables
Copy the template and add your credentials:
```bash
cp .env.example .env
```

**Critical variables to set:**
```bash
# Google Gemini API
GEMINI_API_KEY=your_google_api_key_here

# Rhino Compute (local development)
RHINO_COMPUTE_URL=http://localhost:8081

# Or with Cloudflare Tunnel (production)
RHINO_COMPUTE_URL=https://rhino-api.yourdomain.com
RHINO_COMPUTE_API_KEY=optional_key
```

**Get Gemini API Key:**
1. Visit https://makersuite.google.com/app/apikey
2. Click "Create API key"
3. Copy to `.env` as `GEMINI_API_KEY`

### Step 3: Start Rhino Compute (Windows 10 Pro)

#### Install Rhino 7 or 8 with Compute Server
```powershell
# Download Rhino Compute from:
# https://www.rhino3d.com/download/rhino-compute/latest

# Or install via chocolatey:
choco install rhino-compute
```

#### Start Rhino Compute locally
```powershell
# Default location:
& "C:\Program Files\Rhino\System\RhinoCompute.exe" --localhost --port 8081

# Or as a service (Windows Service)
# Open Services and start "Rhino Compute"
```

Verify it's running:
```bash
curl http://localhost:8081/health
```

### Step 4: Set Up Cloudflare Tunnel (Production)

#### On Windows 10 Pro machine:
```powershell
# Install cloudflared
choco install cloudflare-warp

# Authenticate
cloudflared tunnel login

# Create tunnel for Rhino Compute
cloudflared tunnel create rhino-compute
cloudflared tunnel route dns rhino-compute rhino-api.yourdomain.com

# Configure ingress in ~/.cloudflared/config.yml:
# tunnel: rhino-compute
# credentials-file: /Users/you/.cloudflared/<UUID>.json
# ingress:
#   - hostname: rhino-api.yourdomain.com
#     service: http://localhost:8081
#   - service: http_status:404

# Start tunnel
cloudflared tunnel run rhino-compute
```

#### On Mac Mini:
```bash
# Update .env with tunnel URL
RHINO_COMPUTE_URL=https://rhino-api.yourdomain.com
```

---

## API Integration

### Updated Endpoint: `/cad/generate-from-prompt`

**Before:** Returned CadQuery code
```json
{
  "status": "completed",
  "code": "from cadquery import Workplane\n...",
  "code_type": "cadquery"
}
```

**After:** Returns structured CAD parameters
```json
{
  "status": "completed",
  "extraction_success": true,
  "cad_params": {
    "measurements": {
      "length": 100,
      "width": 50,
      "height": 75,
      "unit": "mm",
      "radius": null
    },
    "shapes": ["cube"],
    "style": {
      "material": "plastic",
      "finish": "smooth",
      "color": "#FFFFFF",
      "transparency": null
    },
    "parameters": {
      "wall_thickness": 2,
      "fillet_radius": 5,
      "texture_pattern": null,
      "custom_params": {}
    },
    "description": "A white plastic cube with smooth finish",
    "confidence": 0.92
  }
}
```

### New Endpoint: `/cad/generate-stl` (coming in Phase 2)
Will integrate Gemini output with Rhino Compute to generate .STL files directly.

---

## Data Flow Example

### User uploads an image of a box:
1. **Image Processing**: `generate_cad_from_image(file_path)`
2. **Gemini Analysis**: Analyzes image dimensions, material, colors
3. **JSON Extraction**: Returns validated `CADExtractionSchema`
4. **Schema Validation**: Pydantic ensures all values are correct types/ranges
5. **API Response**: Structured JSON sent to frontend
6. **[Phase 2]** **Rhino Processing**: Parameters → Grasshopper template → .STL

---

## Testing

### Test Gemini Extraction
```python
import asyncio
from cad_service import generate_cad_from_image

# Test with an image
result = asyncio.run(generate_cad_from_image("./path/to/image.jpg"))
print(result)
```

### Test Rhino Connection
```python
from rhino_client import get_rhino_client

client = get_rhino_client()
health = client.get_health()
print(health)  # Should return {"status": "ok"} if Rhino is running
```

---

## Troubleshooting

### Issue: `GEMINI_API_KEY not found`
**Solution:** Set environment variable in `.env` file or system environment

### Issue: Rhino Compute connection refused
**Solutions:**
- Check Rhino Compute is running: `curl http://localhost:8081/health`
- Check firewall allows port 8081
- For tunnel: Verify `cloudflared tunnel run` is active
- Check tunnel URL in `.env` is correct

### Issue: JSON extraction fails
**Solutions:**
- Ensure response is valid JSON (check raw response)
- Gemini may wrap JSON in markdown - parser handles this
- Check Gemini API quota hasn't been exceeded
- Try simpler prompt/image

---

## Next Steps (Phase 2)

1. **Rhino Compute Integration**: Generate STL from Gemini parameters
2. **Grasshopper Templates**: Create parametric templates for each shape type
3. **Job Queue System**: Track CAD generation jobs with progress
4. **STL Validation**: Verify generated files before delivery
5. **Frontend Updates**: Display extracted parameters, allow editing before generation

---

## Configuration Checklist

- [ ] Google Gemini API key obtained and set in `.env`
- [ ] Rhino Compute installed on Windows machine
- [ ] Rhino Compute running on localhost:8081
- [ ] Cloudflare Tunnel configured (if remote access needed)
- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] FastAPI server can start (`python main.py`)
- [ ] Gemini connectivity verified (test extraction)
- [ ] Rhino connectivity verified (health check)

---

## Security Notes

- Never commit `.env` file with real API keys
- Use `.env.local` for development secrets
- Rhino Compute should only be exposed via Cloudflare Tunnel
- Validate all user inputs before sending to Gemini
- Implement rate limiting on API endpoints
- Monitor Gemini API usage for cost control

---

## Support & Questions

For issues or questions about this implementation:
1. Check `.env` configuration is complete
2. Verify API keys are valid
3. Check network connectivity to Rhino Compute
4. Review application logs for detailed errors
5. Test services individually (Gemini, Rhino) before integration
