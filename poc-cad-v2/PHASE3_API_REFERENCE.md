# Phase 3 API Quick Reference
## Refinement, Batch Processing & Export

**Version:** 3.0.0 | **Status:** ✅ Ready

---

## 🎯 Quick Examples

### Example 1: Generate, Refine, Compare
```bash
# 1. Generate initial model
JOB1=$(curl -s -X POST http://localhost:8000/cad/generate-from-prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "100mm white cube"}' | jq -r '.job_id')
echo "Generated: $JOB1"

# 2. Refine with larger dimensions
JOB2=$(curl -s -X POST http://localhost:8000/cad/refine/$JOB1 \
  -H "Content-Type: application/json" \
  -d '{
    "refinement_type": "update_measurements",
    "updated_params": {
      "measurements": {"length": 150, "width": 150, "height": 150}
    }
  }' | jq -r '.refined_job_id')
echo "Refined: $JOB2"

# 3. Compare quality
curl -s "http://localhost:8000/cad/compare?job_id_1=$JOB1&job_id_2=$JOB2" | jq .

# 4. View history
curl -s http://localhost:8000/cad/history/$JOB1 | jq .
```

### Example 2: Batch Generation (Sequential)
```bash
# Create batch
BATCH=$(curl -s -X POST http://localhost:8000/cad/batch/create \
  -H "Content-Type: application/json" \
  -d '{
    "requests": [
      {"prompt": "100mm cube"},
      {"prompt": "50mm sphere"},
      {"prompt": "75mm cylinder"}
    ],
    "mode": "sequential",
    "max_concurrent": 1
  }' | jq -r '.batch_id')
echo "Batch: $BATCH"

# Process
curl -s -X POST http://localhost:8000/cad/batch/$BATCH/process | jq .

# Get results
curl -s http://localhost:8000/cad/batch/$BATCH/results | jq .
```

### Example 3: Batch Generation (Throttled/Parallel)
```bash
# Parallel mode - all at once
BATCH=$(curl -s -X POST http://localhost:8000/cad/batch/create \
  -H "Content-Type: application/json" \
  -d '{
    "requests": [
      {"prompt": "100mm cube"},
      {"prompt": "50mm sphere"}
    ],
    "mode": "parallel"
  }' | jq -r '.batch_id')

# Throttled mode - max 3 concurrent (good for larger batches)
BATCH=$(curl -s -X POST http://localhost:8000/cad/batch/create \
  -H "Content-Type: application/json" \
  -d '{
    "requests": [
      {"prompt": "model1"},
      {"prompt": "model2"},
      {"prompt": "model3"},
      {"prompt": "model4"},
      {"prompt": "model5"}
    ],
    "mode": "throttled",
    "max_concurrent": 3
  }' | jq -r '.batch_id')

curl -s -X POST http://localhost:8000/cad/batch/$BATCH/process | jq '.summary'
```

### Example 4: Export to Multiple Formats
```bash
# View all available formats
curl -s http://localhost:8000/cad/export/formats | jq '.formats[] | {format, name, extension}'

# Export to OBJ
curl -s -X POST "http://localhost:8000/cad/export/abc123?format=obj&quality=normal" | jq .

# Export to ASCII STL
curl -s -X POST "http://localhost:8000/cad/export/abc123?format=stl_ascii" | jq .

# Download OBJ
curl http://localhost:8000/cad/download/abc123/obj -o model.obj

# Download ASCII STL
curl http://localhost:8000/cad/download/abc123/stl_ascii -o model_ascii.stl
```

---

## 📋 API Endpoints Reference

### Model Refinement

#### POST /cad/refine/{job_id}
Refine existing model with updated parameters
```
Body:
{
  "refinement_type": "update_measurements|update_style|update_parameters|change_shape|full_update",
  "updated_params": {...}
}

Response 200:
{
  "status": "success",
  "original_job_id": "abc123",
  "refined_job_id": "def456",
  "quality_improvement": 3.5,
  "parameters_changed": {...},
  "new_quality_score": 95
}
```

**Refinement Types:**
- `update_measurements` - Modify dimensions
- `update_style` - Change material/color/finish
- `update_parameters` - Wall thickness, fillet, texture
- `change_shape` - Switch shape type
- `full_update` - Replace all parameters

---

#### GET /cad/history/{job_id}
Get all refinement versions of a model
```
Response 200:
{
  "job_id": "abc123",
  "versions": [
    {
      "version_id": "abc123",
      "quality_score": 92,
      "refinement_type": "original",
      "created_at": "..."
    },
    {
      "version_id": "def456",
      "quality_score": 95,
      "refinement_type": "update_measurements",
      "created_at": "..."
    }
  ],
  "total_versions": 2,
  "current_quality": 95
}
```

---

#### GET /cad/compare
Compare two models
```
Query Params:
- job_id_1: First model
- job_id_2: Second model

Response 200:
{
  "comparison": {
    "model_1": {
      "job_id": "abc123",
      "quality_score": 92,
      "triangle_count": 12,
      "file_size_mb": 0.05
    },
    "model_2": {
      "job_id": "def456",
      "quality_score": 95,
      "triangle_count": 14,
      "file_size_mb": 0.06
    },
    "quality_delta": 3,
    "size_delta_mb": 0.01,
    "triangle_delta": 2
  }
}
```

---

### Batch Processing

#### POST /cad/batch/create
Create new batch job
```
Body:
{
  "requests": [
    {"prompt": "..."},
    {"image_path": "..."},
    ...
  ],
  "mode": "sequential|parallel|throttled",
  "max_concurrent": 3
}

Response 201:
{
  "status": "created",
  "batch_id": "batch123",
  "total_requests": 5,
  "mode": "throttled",
  "estimated_time": "1m 40s"
}
```

---

#### POST /cad/batch/{batch_id}/process
Start processing batch
```
Response 200:
{
  "status": "completed",
  "batch_id": "batch123",
  "job_ids": ["job1", "job2", "job3"],
  "results": {...},
  "summary": {
    "total_requests": 3,
    "successful": 3,
    "failed": 0,
    "success_rate": "100%",
    "average_quality_score": "93.7/100"
  }
}
```

---

#### GET /cad/batch/{batch_id}/status
Check batch processing status
```
Response 200:
{
  "batch_id": "batch123",
  "status": "processing",
  "total_requests": 5,
  "completed_jobs": 2,
  "job_ids": ["job1", "job2"],
  "created_at": "...",
  "started_at": "...",
  "completed_at": null
}
```

---

#### GET /cad/batch/{batch_id}/results
Get batch results (detailed)
```
Query Params:
- details: false (default) - job IDs only
- details: true - full result objects

Response 200:
{
  "batch_id": "batch123",
  "status": "completed",
  "total_jobs": 3,
  "jobs": [
    {
      "job_id": "job1",
      "result": {...}
    }
  ]
}
```

---

#### GET /cad/batch/{batch_id}/manifest
Get batch manifest (export-ready)
```
Response 200:
{
  "batch_id": "batch123",
  "created_at": "...",
  "status": "completed",
  "mode": "throttled",
  "requests": [
    {
      "index": 1,
      "type": "prompt",
      "content": "100mm cube",
      "job_id": "job1",
      "result": {...}
    }
  ]
}
```

---

### Export & Download

#### GET /cad/export/formats
List all supported export formats
```
Response 200:
{
  "formats": [
    {
      "format": "stl_binary",
      "name": "STL Binary",
      "extension": ".stl",
      "description": "...",
      "suitable_for": ["3D printing", "CAM", "simulation"],
      "file_size_estimate": "1.5x original"
    },
    {
      "format": "obj",
      "name": "Wavefront OBJ",
      "extension": ".obj",
      "quality_levels": ["draft", "normal", "production"]
    },
    ...
  ]
}
```

---

#### POST /cad/export/{job_id}
Export model to format
```
Query Params:
- format: Target format (stl_binary, stl_ascii, obj, step, iges, vrml)
- quality: Quality level (draft, normal, production) - for obj only

Response 200:
{
  "status": "success",
  "format": "obj",
  "quality": "normal",
  "file_path": "/cad_models/abc123/model_obj.obj",
  "file_size_mb": 0.45,
  "vertex_count": 36
}

Response (Rhino required):
{
  "status": "requires_rhino",
  "format": "step",
  "message": "STEP export requires Rhino Compute",
  "instructions": [...]
}
```

---

#### GET /cad/download/{job_id}/{format}
Download exported file
```
Path Params:
- job_id: Model job ID
- format: Export format (obj, stl_ascii, stl_binary, etc)

Response 200:
(Binary file with appropriate Content-Type)

Content-Type Headers:
- stl_binary, stl_ascii: model/stl
- obj: model/obj
- step: model/step
- iges: model/iges

Filename: model_{job_id}.{ext}
```

---

## 📊 Status Codes & Errors

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Model refined, batch created |
| 201 | Created | Batch job created |
| 400 | Bad request | Invalid format, missing params |
| 404 | Not found | Job/batch doesn't exist |
| 422 | Validation error | Invalid refinement type |
| 500 | Server error | Rhino connection failed |

---

## 🔄 Common Workflows

### Workflow: Single Model Iteration
```
1. Generate
   POST /cad/generate-from-prompt

2. View Results
   GET /cad/job/{job_id}

3. Refine
   POST /cad/refine/{job_id}

4. Compare
   GET /cad/compare?job_id_1=old&job_id_2=new

5. History
   GET /cad/history/{job_id}

6. Export
   POST /cad/export/{job_id}?format=obj

7. Download
   GET /cad/download/{job_id}/obj
```

### Workflow: Batch Production
```
1. Create Batch
   POST /cad/batch/create
   (100 models, throttled mode)

2. Start Processing
   POST /cad/batch/{batch_id}/process
   (Estimated: 25 minutes)

3. Monitor
   GET /cad/batch/{batch_id}/status
   (Poll every 10 seconds)

4. Get Results
   GET /cad/batch/{batch_id}/results?details=true

5. Export Manifest
   GET /cad/batch/{batch_id}/manifest

6. Download All
   for job_id in results:
     GET /cad/download/{job_id}/stl_binary
```

### Workflow: Format Conversion
```
1. Generate Model (STL)
   POST /cad/generate-from-prompt

2. Export to OBJ
   POST /cad/export/{job_id}?format=obj

3. Export to ASCII STL
   POST /cad/export/{job_id}?format=stl_ascii

4. View Formats
   GET /cad/export/formats

5. Download Multiple
   GET /cad/download/{job_id}/obj
   GET /cad/download/{job_id}/stl_ascii
```

---

## 🚀 Performance Tips

### For Batch Processing
- **Small batches (< 10):** Use `parallel` mode (all at once)
- **Medium batches (10-50):** Use `throttled` mode with max_concurrent=3-5
- **Large batches (> 50):** Use `throttled` mode with max_concurrent=2-3, consider splitting

### For Refinement
- **Quick edits:** Update only changed parameters (not full_update)
- **Major changes:** Use full_update for fresh regeneration
- **Multiple iterations:** Build on previous refinements (quality may accumulate)

### For Export
- **Quick review:** Use `draft` quality for OBJ
- **Production:** Use `normal` or `production` quality
- **File size critical:** Use `stl_ascii` (smaller than binary for simple models)

---

## 🔗 Integration with Phase 1 & 2

**Phase 1 Still Provides:**
- Image to JSON extraction (Gemini Vision)
- Prompt to JSON generation
- Schema validation

**Phase 2 Still Provides:**
- Rhino Compute integration
- STL generation
- Quality validation & scoring

**Phase 3 Adds On Top:**
- Model refinement (reuses Phase 1 extraction)
- Batch orchestration (calls Phase 2 multiple times)
- Format conversion (post-processes Phase 2 output)

---

## ⚠️ Known Limitations

### Current (Phase 3)
- STEP/IGES export requires Rhino Compute setup
- VRML export is placeholder
- Batch size limited by system memory
- Version tree is linear (no branching)

### Planned (Phase 4)
- Web 3D viewer for STL visualization
- Frontend parameter editor
- Advanced analytics dashboard
- Collaborative refinement

---

## 📞 Troubleshooting

### Batch Not Processing
```
Problem: POST /batch/{id}/process returns error
Solution: Check /batch/{id}/status first
         Ensure all requests have valid format
```

### Export Fails with "requires_rhino"
```
Problem: Cannot export to STEP format
Solution: STEP/IGES require Rhino Compute
         Use STL_ASCII, STL_BINARY, or OBJ instead
         Rhino integration planned for Phase 4
```

### File Not Found After Export
```
Problem: GET /download/{job_id}/format returns 404
Solution: First run POST /export/{job_id}?format=...
         Check format name is correct
         Verify job_id exists with GET /job/{job_id}
```

---

## 📚 Documentation Links

- [PHASE3_IMPLEMENTATION.md](../PHASE3_IMPLEMENTATION.md) - Full technical guide
- [PHASE3_COMPLETION.md](../PHASE3_COMPLETION.md) - Completion summary
- [PHASE2_API_REFERENCE.md](../PHASE2_API_REFERENCE.md) - Phase 2 endpoints
- [PHASE1_IMPLEMENTATION.md](../PHASE1_IMPLEMENTATION.md) - Phase 1 setup

---

**Phase 3 Ready: Test and Integrate ✨**
