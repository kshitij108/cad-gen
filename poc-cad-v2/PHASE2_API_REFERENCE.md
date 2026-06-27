# Phase 2 Quick Reference
## API Endpoints & Architecture

**Status:** ✅ Phase 2 Complete | **Version:** 2.0.0

---

## 🚀 Quick Start

### Install & Run
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### API Documentation
```
Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
```

---

## 📡 Phase 2 API Endpoints

### Generation Endpoints

#### 1. Generate from Text Prompt
```
POST /cad/generate-from-prompt
Content-Type: application/json

{
  "prompt": "a 100mm white plastic cube with smooth finish"
}

Response:
{
  "status": "success",
  "job_id": "abc123",
  "cad_parameters": {...},
  "template": {...},
  "stl_validation": {...},
  "quality_score": 95,
  "file_url": "/cad/download/abc123"
}
```

#### 2. Generate from Image
```
POST /cad/generate-from-image
Content-Type: multipart/form-data

file: @reference.jpg

Response: (same as above)
```

#### 3. Generate from Sketch
```
POST /cad/generate-from-sketch
Content-Type: multipart/form-data

file: @sketch.png

Response: (same as above)
```

---

### Template Management

#### 4. List All Templates
```
GET /cad/templates

Response:
{
  "status": "success",
  "templates": [
    {
      "template_id": "template_cube_v1",
      "shape": "cube",
      "description": "...",
      "input_parameters": {...}
    },
    ...
  ],
  "total": 6
}
```

#### 5. List Templates for Specific Shape
```
GET /cad/templates/{shape}

Shapes: cube, sphere, cylinder, cone, wedge, torus

Example: GET /cad/templates/sphere
```

---

### Job Status & Details

#### 6. Get Job Status
```
GET /cad/job/{job_id}

Response:
{
  "job_id": "abc123",
  "status": "completed",
  "progress": 100,
  "stage": "completed",
  "job_type": "prompt",
  "cad_parameters": {...},
  "stl_validation": {...},
  "file_url": "/cad/download/abc123",
  "created_at": "2026-06-26T..."
}
```

#### 7. Get Extraction Parameters
```
GET /cad/job/{job_id}/extraction

Response:
{
  "job_id": "abc123",
  "extracted_parameters": {
    "measurements": {
      "length": 100,
      "width": 100,
      "height": 100,
      "unit": "mm"
    },
    "shapes": ["cube"],
    "style": {
      "material": "plastic",
      "finish": "smooth",
      "color": "#FFFFFF"
    },
    "confidence": 0.95
  }
}
```

#### 8. Get STL Validation
```
GET /cad/job/{job_id}/validation

Response:
{
  "job_id": "abc123",
  "validation": {
    "is_valid": true,
    "file_size_mb": 0.05,
    "triangle_count": 12,
    "quality_score": 98,
    "bounds": {
      "x_min": 0, "x_max": 100,
      "y_min": 0, "y_max": 100,
      "z_min": 0, "z_max": 100
    },
    "issues": [],
    "warnings": []
  }
}
```

#### 9. Get Grasshopper Inputs
```
GET /cad/job/{job_id}/grasshopper-inputs

Response:
{
  "job_id": "abc123",
  "grasshopper_inputs": {
    "Length": 100,
    "Width": 100,
    "Height": 100,
    "Material": "plastic",
    "Finish": "smooth",
    "Color": "#FFFFFF"
  }
}
```

---

### Download & Utilities

#### 10. Download STL File
```
GET /cad/download/{job_id}

Returns: Binary STL file
Content-Type: model/stl
Filename: model_{job_id}.stl
```

#### 11. Validate Extraction (Test)
```
POST /cad/validate-extraction
Content-Type: application/json

{
  "measurements": {"length": 100, "width": 50, "height": 75},
  "shapes": ["cube"],
  "style": {...}
}

Response:
{
  "is_valid": true,
  "errors": [],
  "parameters": {...}
}
```

---

## 📊 Data Structures

### CAD Parameters (Gemini Output)
```json
{
  "measurements": {
    "length": 100,
    "width": 50,
    "height": 75,
    "unit": "mm",
    "radius": null,
    "diameter": null
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
  "description": "A white plastic cube",
  "confidence": 0.95
}
```

### Job Status Values
```
Processing: initializing → extracting → validating → converting → generating → finalizing
Terminal: completed, failed
```

### Quality Score Calculation
```
Base: 100 points
- Issue penalty: -20 per issue
- Warning penalty: -5 per warning
- File size penalty: -10 (if >50MB)
- Triangle count penalty: -5 (if >1M)
Result: 0-100 score
```

---

## 🔄 Typical Request Flow

### 1. Submit Request
```bash
curl -X POST http://localhost:8000/cad/generate-from-prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a white cube"}'
```

**Response:** Returns job_id (async processing starts)

### 2. Poll Status
```bash
# Repeat every 1-2 seconds until complete
curl http://localhost:8000/cad/job/{job_id}
```

**Response:** Status with progress (0-100%)

### 3. Download Result (when complete)
```bash
curl http://localhost:8000/cad/download/{job_id} -o model.stl
```

**Response:** Binary STL file

---

## 🛠️ Testing Endpoints

### Using curl
```bash
# Test templates
curl http://localhost:8000/cad/templates | jq .

# Generate from prompt
JOB=$(curl -X POST http://localhost:8000/cad/generate-from-prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "cube"}' | jq -r '.job_id')

# Check status
curl http://localhost:8000/cad/job/$JOB | jq .

# Get validation
curl http://localhost:8000/cad/job/$JOB/validation | jq .

# Download
curl http://localhost:8000/cad/download/$JOB -o model.stl
```

### Using Python
```python
import requests
import json
import time

BASE_URL = "http://localhost:8000"

# Generate
resp = requests.post(f"{BASE_URL}/cad/generate-from-prompt", json={
    "prompt": "a 50mm white sphere"
})
job_id = resp.json()["job_id"]
print(f"Job ID: {job_id}")

# Poll
for _ in range(60):
    status = requests.get(f"{BASE_URL}/cad/job/{job_id}").json()
    print(f"Progress: {status['progress']}% - Stage: {status['stage']}")
    
    if status['status'] == 'completed':
        print(f"Quality Score: {status['stl_validation']['quality_score']}/100")
        break
    elif status['status'] == 'failed':
        print(f"Error: {status.get('error')}")
        break
    
    time.sleep(1)

# Download
if status['status'] == 'completed':
    stl_data = requests.get(f"{BASE_URL}/cad/download/{job_id}").content
    with open("model.stl", "wb") as f:
        f.write(stl_data)
    print("Downloaded: model.stl")
```

---

## 📝 Configuration (Phase 2)

### Environment Variables
```bash
# Gemini API (Phase 1)
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-1.5-pro

# Rhino Compute (Phase 2)
RHINO_COMPUTE_URL=https://rhino-api.yourdomain.com

# File Management (Phase 2)
UPLOAD_MAX_FILE_SIZE=52428800  # 50MB
CAD_OUTPUT_DIRECTORY=./cad_models
```

---

## 🎯 Common Patterns

### Pattern 1: Generate & Download
```python
result = requests.post(f"{url}/cad/generate-from-prompt", 
                       json={"prompt": "cube"})
job_id = result.json()["job_id"]

# Poll until complete
while True:
    status = requests.get(f"{url}/cad/job/{job_id}").json()
    if status["status"] in ["completed", "failed"]:
        break
    time.sleep(1)

# Download if successful
if status["status"] == "completed":
    stl = requests.get(f"{url}/cad/download/{job_id}").content
```

### Pattern 2: Check Quality
```python
validation = requests.get(f"{url}/cad/job/{job_id}/validation").json()
score = validation["validation"]["quality_score"]

if score >= 90:
    print("Excellent quality")
elif score >= 75:
    print("Good quality")
else:
    print("Review required")
```

### Pattern 3: Iterate Parameters
```python
# Get current parameters
params = requests.get(f"{url}/cad/job/{job_id}/extraction").json()

# Validate modified parameters
modified = params["extracted_parameters"]
modified["measurements"]["height"] = 150

result = requests.post(f"{url}/cad/validate-extraction", json=modified)
if result.json()["is_valid"]:
    # Regenerate with new parameters
    # (Feature for Phase 3)
    pass
```

---

## 📊 Monitoring

### Check API Health
```bash
curl http://localhost:8000/  # Should return version info
```

### View API Documentation
```
Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
```

### Monitor Job Progress
```bash
# Watch a job's progress in real-time
watch -n 1 "curl -s http://localhost:8000/cad/job/abc123 | jq '.progress'"
```

---

## ⚠️ Error Codes

| Status Code | Meaning |
|------------|---------|
| 200 | Success |
| 400 | Bad request (invalid params) |
| 404 | Resource not found (job_id invalid) |
| 500 | Server error (contact support) |

---

## 🔗 Phase 2 Architecture

```
Frontend
   ↓
[API Gateway]
   ↓
┌─────────────────────────────────────┐
│  FastAPI Application (v2.0.0)       │
├─────────────────────────────────────┤
│ Route Layer (11 endpoints)          │
│  - /cad/generate-*                  │
│  - /cad/templates                   │
│  - /cad/job/*                       │
│  - /cad/download/*                  │
└─────────────────────────────────────┘
   ↓
┌─────────────────────────────────────┐
│ Pipeline Orchestrator               │
│  - cad_pipeline.py                  │
│  - 6 pipeline stages                │
└─────────────────────────────────────┘
   ↓ ↓ ↓
  ┌─────────┬──────────┬──────────┐
  │ Gemini  │ Registry │ Validator│
  │ Vision  │ (6 tmpl) │ (STL)    │
  └────┬────┴────┬─────┴────┬─────┘
       ↓         ↓          ↓
   [Rhino Compute] ← Grasshopper Templates
```

---

## 🎓 Next Steps

1. **Create Grasshopper Templates** - .gh files for shapes
2. **Frontend UI** - Parameter editor, 3D viewer
3. **Batch Processing** - Multiple models at once
4. **Model Refinement** - Edit and regenerate
5. **Export Options** - STEP, OBJ formats

---

**Phase 2 Complete ✨ Ready for Production Testing**
