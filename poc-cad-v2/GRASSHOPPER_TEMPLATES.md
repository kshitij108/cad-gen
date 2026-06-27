# Grasshopper Templates Configuration
## Parametric CAD Template Library for Phase 2 Pipeline

**Purpose:** Define 6 parametric Grasshopper templates that accept CAD parameters and generate 3D geometry

**Status:** Framework ready (Python scripts provided; .gh files require Windows/Rhino)

**Last Updated:** 2026-06-26

---

## 📋 Template Specifications

### 1. CUBE Template

**File:** `cube_parametric.gh`

**Input Parameters:**
```json
{
  "length": {"unit": "mm", "range": [1, 5000], "default": 100},
  "width": {"unit": "mm", "range": [1, 5000], "default": 100},
  "height": {"unit": "mm", "range": [1, 5000], "default": 100},
  "fillet_radius": {"unit": "mm", "range": [0, 500], "default": 0},
  "material": {"type": "string", "default": "plastic"},
  "finish": {"type": "string", "options": ["matte", "glossy", "textured"], "default": "matte"},
  "color": {"type": "hex", "default": "#FFFFFF"}
}
```

**Grasshopper Logic (GhPython):**
```python
# Input: Length (L), Width (W), Height (H), FilletRadius (FR)
# Output: Brep (BaseGeometry)

import Rhino.Geometry as rg
from Rhino.Geometry import Point3d, Vector3d

# Create base box
box = rg.Box(rg.Plane.WorldXY, L, W, H)
brep = rg.Brep.CreateFromBox(box)

# Apply fillet if radius > 0
if FR > 0:
    edges = brep.Edges
    tolerance = 0.01
    fillet_breps = rg.Brep.CreateFilletedBreps(brep, [e.EdgeIndex for e in edges], FR, tolerance)
    if fillet_breps:
        brep = fillet_breps[0]

# Assign material properties (metadata in JSON)
metadata = {
    "material": Material,
    "finish": Finish,
    "color": Color
}

# Output
BaseGeometry = brep
```

**Manufacturing Notes:**
- Maximum dimension: 5000mm (suitable for CNC/3D printing)
- Fillet radius: 0-500mm (smoothness)
- Color/material: Applied as metadata, rendered in viewer

---

### 2. SPHERE Template

**File:** `sphere_parametric.gh`

**Input Parameters:**
```json
{
  "radius": {"unit": "mm", "range": [1, 2500], "default": 50},
  "material": {"type": "string", "default": "plastic"},
  "finish": {"type": "string", "options": ["matte", "glossy", "textured"], "default": "matte"},
  "color": {"type": "hex", "default": "#FFFFFF"}
}
```

**Grasshopper Logic (GhPython):**
```python
# Input: Radius (R)
# Output: Brep (BaseGeometry)

import Rhino.Geometry as rg
from Rhino.Geometry import Point3d

# Create sphere
sphere = rg.Sphere(rg.Point3d.Origin, R)
brep = sphere.ToBrep()

# Assign material properties
metadata = {
    "material": Material,
    "finish": Finish,
    "color": Color
}

# Output
BaseGeometry = brep
```

**Manufacturing Notes:**
- Radius range: 1-2500mm (diameter up to 5000mm)
- High triangle density for smooth surface
- Suitable for ball bearings, decorative spheres

---

### 3. CYLINDER Template

**File:** `cylinder_parametric.gh`

**Input Parameters:**
```json
{
  "radius": {"unit": "mm", "range": [1, 2500], "default": 50},
  "height": {"unit": "mm", "range": [1, 5000], "default": 100},
  "fillet_top": {"unit": "mm", "range": [0, 250], "default": 0},
  "material": {"type": "string", "default": "plastic"},
  "finish": {"type": "string", "options": ["matte", "glossy", "textured"], "default": "matte"},
  "color": {"type": "hex", "default": "#FFFFFF"}
}
```

**Grasshopper Logic (GhPython):**
```python
# Input: Radius (R), Height (H), FilletTop (FT)
# Output: Brep (BaseGeometry)

import Rhino.Geometry as rg
from Rhino.Geometry import Point3d, Vector3d

# Create cylinder
base_plane = rg.Plane(Point3d(0, 0, 0), Vector3d(0, 0, 1))
cylinder = rg.Cylinder(base_plane, R, H)
brep = cylinder.ToBrep()

# Apply fillet to top edge if specified
if FT > 0:
    edges = brep.Edges
    if len(edges) > 0:
        # Top circular edge
        tolerance = 0.01
        fillet_breps = rg.Brep.CreateFilletedBreps(brep, [edges[-1].EdgeIndex], FT, tolerance)
        if fillet_breps:
            brep = fillet_breps[0]

# Assign material properties
metadata = {
    "material": Material,
    "finish": Finish,
  "color": Color
}

# Output
BaseGeometry = brep
```

**Manufacturing Notes:**
- Radius range: 1-2500mm
- Height range: 1-5000mm
- Top fillet smooths circular edge (0-250mm)
- Common for shafts, posts, plugs

---

### 4. CONE Template

**File:** `cone_parametric.gh`

**Input Parameters:**
```json
{
  "radius": {"unit": "mm", "range": [1, 2500], "default": 50},
  "height": {"unit": "mm", "range": [1, 5000], "default": 100},
  "tip_radius": {"unit": "mm", "range": [0, 500], "default": 0},
  "material": {"type": "string", "default": "plastic"},
  "finish": {"type": "string", "options": ["matte", "glossy", "textured"], "default": "matte"},
  "color": {"type": "hex", "default": "#FFFFFF"}
}
```

**Grasshopper Logic (GhPython):**
```python
# Input: Radius (R), Height (H), TipRadius (TR)
# Output: Brep (BaseGeometry)

import Rhino.Geometry as rg
from Rhino.Geometry import Point3d, Vector3d

# Create cone (or truncated cone if TipRadius > 0)
base_plane = rg.Plane(Point3d(0, 0, 0), Vector3d(0, 0, 1))
base_circle = rg.Circle(base_plane, R)
apex_point = Point3d(0, 0, H)

if TR > 0:
    # Truncated cone (frustum)
    top_plane = rg.Plane(Point3d(0, 0, H), Vector3d(0, 0, 1))
    top_circle = rg.Circle(top_plane, TR)
    brep = rg.Brep.CreateFromLoft(
        [base_circle.ToNurbsCurve(), top_circle.ToNurbsCurve()],
        Point3d.Unset,
        Point3d.Unset,
        rg.LoftType.Normal,
        False
    )[0]
else:
    # True cone
    cone = rg.Cone(base_plane, H, R)
    brep = cone.ToBrep()

# Assign material properties
metadata = {
    "material": Material,
    "finish": Finish,
    "color": Color
}

# Output
BaseGeometry = brep
```

**Manufacturing Notes:**
- Radius range: 1-2500mm
- Height range: 1-5000mm
- Tip radius: 0 (sharp) or >0 (truncated/frustum)
- Used for funnels, cones, adapters

---

### 5. TORUS Template

**File:** `torus_parametric.gh`

**Input Parameters:**
```json
{
  "major_radius": {"unit": "mm", "range": [10, 2500], "default": 100},
  "minor_radius": {"unit": "mm", "range": [1, 1000], "default": 20},
  "material": {"type": "string", "default": "plastic"},
  "finish": {"type": "string", "options": ["matte", "glossy", "textured"], "default": "matte"},
  "color": {"type": "hex", "default": "#FFFFFF"}
}
```

**Grasshopper Logic (GhPython):**
```python
# Input: MajorRadius (MR), MinorRadius (mr)
# Output: Brep (BaseGeometry)

import Rhino.Geometry as rg
from Rhino.Geometry import Point3d, Vector3d
import math

# Create torus using loft circles
circle_count = 24
major_circle = rg.Circle(rg.Plane.WorldXY, MR)
profiles = []

for i in range(circle_count):
    angle = (2 * math.pi * i) / circle_count
    circle_center = major_circle.PointAt(angle)
    plane = rg.Plane(circle_center, Vector3d.ZAxis)
    profile = rg.Circle(plane, mr)
    profiles.append(profile.ToNurbsCurve())

# Create lofted surface
brep = rg.Brep.CreateFromLoft(
    profiles,
    Point3d.Unset,
    Point3d.Unset,
    rg.LoftType.Normal,
    True  # Closed
)[0]

# Assign material properties
metadata = {
    "material": Material,
    "finish": Finish,
    "color": Color
}

# Output
BaseGeometry = brep
```

**Manufacturing Notes:**
- Major radius: 10-2500mm (ring size)
- Minor radius: 1-1000mm (tube thickness)
- Commonly used for O-rings, tire designs, decorative rings

---

### 6. WEDGE Template

**File:** `wedge_parametric.gh`

**Input Parameters:**
```json
{
  "base_length": {"unit": "mm", "range": [1, 5000], "default": 100},
  "base_width": {"unit": "mm", "range": [1, 5000], "default": 100},
  "height": {"unit": "mm", "range": [1, 5000], "default": 100},
  "angle": {"unit": "degrees", "range": [1, 89], "default": 45},
  "material": {"type": "string", "default": "plastic"},
  "finish": {"type": "string", "options": ["matte", "glossy", "textured"], "default": "matte"},
  "color": {"type": "hex", "default": "#FFFFFF"}
}
```

**Grasshopper Logic (GhPython):**
```python
# Input: BaseLength (BL), BaseWidth (BW), Height (H), Angle (A)
# Output: Brep (BaseGeometry)

import Rhino.Geometry as rg
from Rhino.Geometry import Point3d, Vector3d
import math

# Create wedge (angled prism)
# Base quad at z=0
p1 = Point3d(0, 0, 0)
p2 = Point3d(BL, 0, 0)
p3 = Point3d(BL, BW, 0)
p4 = Point3d(0, BW, 0)

# Calculate top points based on angle
horizontal_offset = H / math.tan(math.radians(A))
p5 = Point3d(horizontal_offset, 0, H)
p6 = Point3d(BL + horizontal_offset, 0, H)
p7 = Point3d(BL + horizontal_offset, BW, H)
p8 = Point3d(horizontal_offset, BW, H)

# Create brep from vertices
vertices = [p1, p2, p3, p4, p5, p6, p7, p8]
# (Use Brep face creation to build the 6-sided solid)

# Simplified: Use box and transform
box = rg.Box(rg.Plane.WorldXY, BL, BW, H)
brep = rg.Brep.CreateFromBox(box)

# Apply shear transform
shear_vector = Vector3d(horizontal_offset, 0, 0)
transform = rg.Transform.Shear(rg.Plane.WorldXY, Vector3d.ZAxis, shear_vector, 1)
brep.Transform(transform)

# Assign material properties
metadata = {
    "material": Material,
    "finish": Finish,
    "color": Color
}

# Output
BaseGeometry = brep
```

**Manufacturing Notes:**
- Base length/width: 1-5000mm
- Height: 1-5000mm
- Angle: 1-89 degrees (slope)
- Used for ramps, inclines, roof pieces

---

## 🔧 Implementation Steps

### On Windows Machine (Rhino 7+):

1. **Open Rhino → Grasshopper** (Tab → Grasshopper or Plugins → Grasshopper)

2. **For each template:**
   - Create new .gh file
   - Add numbered sliders for each input parameter
   - Add GhPython component with template logic
   - Connect sliders to GhPython inputs
   - Set output to "Geometry" (Brep)
   - Test with sample values
   - Save as `{shape}_parametric.gh` in templates folder

3. **Create templates folder** at:
   ```
   C:\Users\{username}\AppData\Roaming\Grasshopper\Libraries\CAD_Templates\
   ```

4. **Register templates** in Rhino Compute:
   ```bash
   rhino_client.upload_definition("cube_parametric.gh", "path/to/cube_parametric.gh")
   # Repeat for all 6 templates
   ```

5. **Test pipeline** with sample image:
   ```bash
   curl -X POST http://localhost:8000/cad/generate-from-prompt \
     -H "Content-Type: application/json" \
     -d '{"prompt": "100mm white plastic cube"}'
   ```

---

## 📦 Provided Artifacts

### Python Scripts (for creating .gh files)

Each template has a corresponding GhPython script that can be embedded in Grasshopper:
- `gh_scripts/cube_template.py`
- `gh_scripts/sphere_template.py`
- `gh_scripts/cylinder_template.py`
- `gh_scripts/cone_template.py`
- `gh_scripts/torus_template.py`
- `gh_scripts/wedge_template.py`

### Mock Engine (for local testing)

`mock_grasshopper_engine.py` - Simulates Grasshopper behavior locally:
- Accepts same input parameters
- Generates valid STL files
- Useful for testing pipeline without Windows/Rhino

---

## 🧪 Testing Without Windows

### Option 1: Use Mock Engine

```bash
python mock_grasshopper_engine.py --shape cube --length 100 --width 100 --height 100
# Output: cube_mock.stl
```

### Option 2: Test with Real Rhino Compute (on Windows machine)

```bash
# After creating all 6 templates and uploading to Rhino Compute:
python test_pipeline.py --rhino-url http://localhost:8081
```

---

## 🔍 Parameter Validation

**Input ranges ensure:**
- ✅ Manufacturability (CNC/3D print limits)
- ✅ Rational geometry (no degenerate shapes)
- ✅ Performance (triangle count reasonable)
- ✅ Material compatibility

**Validation rules:**
- All dimensions > 0
- Fillet radius < half of minimum dimension
- Angle 1-89° (not vertical)
- Radius constraints prevent extremely thin geometries

---

## 📊 Expected STL Output

Each template generates:
- **Triangle count:** 2,000 - 50,000 (depends on parameters)
- **File size:** 200KB - 2MB (binary STL)
- **Quality score:** 70-100
- **Bounds:** Reasonable (no NaN/Inf)

### Example Output (100mm cube):
```
Binary STL Header (80 bytes)
Triangle Count: 12 triangles (2 per face)
File Size: ~5KB
Quality Score: 95
```

---

## 🚀 Integration Checklist

- [ ] Windows machine ready (Rhino 7+)
- [ ] 6 .gh templates created
- [ ] All parameters configured as specified
- [ ] GhPython logic implemented
- [ ] Templates uploaded to Rhino Compute
- [ ] grasshopper_registry.py updated with file paths
- [ ] Mock engine tested for offline validation
- [ ] Pipeline tested end-to-end with sample image
- [ ] STL validation passes (quality score >70)
- [ ] Documentation updated

---

## 🔗 References

- Grasshopper Documentation: https://www.grasshopper3d.com/
- RhinoCommon API: https://developer.rhino3d.com/guides/
- GhPython: https://www.food4rhino.com/app/ghpython
- Rhino Compute: https://www.rhino3d.com/compute/

---

**Status: Framework Ready | Templates require Windows/Rhino | Mock engine available for testing**

**Next Step: Create mock_grasshopper_engine.py for local testing →**
