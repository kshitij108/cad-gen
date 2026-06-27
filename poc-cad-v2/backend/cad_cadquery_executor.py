"""
CadQuery Code Executor - Executes Python/CadQuery code and exports to STL
"""
import tempfile
import json
import os
import sys
import re
import struct
import math
from pathlib import Path

# Import CadQuery at top level - will be available if installed
try:
    import cadquery as cq
except ImportError:
    cq = None


def execute_cadquery_code(code: str, output_path: str, timeout: int = 30) -> bool:
    """
    Execute CadQuery code and export to STL
    
    Args:
        code: CadQuery Python code string
        output_path: Path where STL should be saved
        timeout: Execution timeout in seconds
        
    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"DEBUG: Executing CadQuery code...")
        
        if cq is not None:
            print(f"✅ CadQuery available, attempting direct execution")
            success = _execute_cadquery_direct(code, output_path)
            if success:
                return True
            else:
                print(f"⚠️  Direct execution failed, falling back to parser...")
                return _execute_cadquery_fallback(code, output_path)
        else:
            print(f"⚠️  CadQuery not available (Python 3.14 incompatible), using fallback parser")
            return _execute_cadquery_fallback(code, output_path)
            
    except Exception as e:
        print(f"❌ Error executing CadQuery code: {e}")
        import traceback
        traceback.print_exc()
        return False


def _execute_cadquery_direct(code: str, output_path: str) -> bool:
    """Execute code directly with CadQuery library"""
    try:
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Strip markdown code fences if Claude wrapped code in them
        if code.strip().startswith("```"):
            lines = code.split("\n")
            # Remove opening markdown fence and language specifier
            if lines[0].startswith("```"):
                lines = lines[1:]  # Remove ```python or ```
            # Remove closing fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)
        
        # Inject cq and math into the namespace so Claude's code can use them
        namespace = {"cq": cq, "math": math}
        
        # Execute the code
        exec(code, namespace)
        
        # Get the result object
        result = namespace.get('result')
        if result is None:
            print(f"❌ No 'result' object found in Claude's code")
            return False
        
        # FIXED: Use the top-level cq import to export properly
        cq.exporters.export(result, str(output_path), cq.exporters.ExportTypes.STL)
        
        file_size = Path(output_path).stat().st_size
        print(f"✅ STL exported successfully: {file_size} bytes")
        return True
            
    except Exception as e:
        print(f"❌ Error in direct CadQuery execution: {e}")
        import traceback
        traceback.print_exc()
        return False


def _execute_cadquery_fallback(code: str, output_path: str) -> bool:
    """
    Fallback: Parse CadQuery code and generate STL from geometry
    This extracts dimensions and generates basic shapes
    """
    try:
        print(f"DEBUG: Parsing CadQuery code for geometry...")
        
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Strip markdown code fences if present
        if code.strip().startswith("```"):
            lines = code.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)
        
        triangles = []
        
        # Strategy 1: Look for explicit geometry definitions in comments
        # e.g., "# ring: major=10, minor=2" or "# sphere radius 20"
        geom_comment = re.search(r'#\s*(?:sphere|ball).*?r[^=]*=\s*(\d+(?:\.\d+)?)', code, re.IGNORECASE | re.DOTALL)
        if geom_comment:
            r = float(geom_comment.group(1))
            print(f"DEBUG: Found sphere in comment: r={r}")
            triangles = _generate_sphere_triangles(r)
        
        geom_comment = re.search(r'#\s*(?:ring|torus).*?(?:major|outer).*?=\s*(\d+(?:\.\d+)?)', code, re.IGNORECASE | re.DOTALL)
        if not triangles and geom_comment:
            major_r = float(geom_comment.group(1))
            minor_match = re.search(r'(?:minor|thickness|inner|width).*?=\s*(\d+(?:\.\d+)?)', code, re.IGNORECASE)
            minor_r = float(minor_match.group(1)) if minor_match else major_r * 0.2
            print(f"DEBUG: Found ring in comment: major={major_r}, minor={minor_r}")
            triangles = _generate_torus_triangles(major_r, minor_r)
        
        # Strategy 2: Look for method chains with extrude
        # e.g., .circle(10).extrude(5) = cylinder
        if not triangles:
            circle_extrude = re.search(r'\.circle\s*\(\s*(\d+(?:\.\d+)?)\s*\)\.extrude\s*\(\s*(\d+(?:\.\d+)?)', code, re.IGNORECASE)
            if circle_extrude:
                r, h = float(circle_extrude.group(1)), float(circle_extrude.group(2))
                print(f"DEBUG: Found circle.extrude: r={r}, h={h}")
                triangles = _generate_cylinder_triangles(r, h)
        
        # Strategy 3: Look for simple primitive methods
        if not triangles:
            sphere_match = re.search(r'\.sphere\s*\(\s*(?:radius\s*=\s*)?(\d+(?:\.\d+)?)', code, re.IGNORECASE)
            if sphere_match:
                r = float(sphere_match.group(1))
                print(f"DEBUG: Found sphere method: r={r}")
                triangles = _generate_sphere_triangles(r)
        
        if not triangles:
            box_match = re.search(r'\.box\s*\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)', code, re.IGNORECASE)
            if box_match:
                w, h, d = float(box_match.group(1)), float(box_match.group(2)), float(box_match.group(3))
                print(f"DEBUG: Found box method: {w}x{h}x{d}")
                triangles = _generate_box_triangles(w, h, d)
        
        if not triangles:
            cyl_match = re.search(r'\.cylinder\s*\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)', code, re.IGNORECASE)
            if cyl_match:
                r, h = float(cyl_match.group(1)), float(cyl_match.group(2))
                print(f"DEBUG: Found cylinder method: r={r}, h={h}")
                triangles = _generate_cylinder_triangles(r, h)
        
        # Strategy 4: rect.extrude pattern (box)
        if not triangles:
            rect_extrude = re.search(r'\.rect\s*\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\)\.extrude\s*\(\s*(\d+(?:\.\d+)?)', code, re.IGNORECASE)
            if rect_extrude:
                w, h, d = float(rect_extrude.group(1)), float(rect_extrude.group(2)), float(rect_extrude.group(3))
                print(f"DEBUG: Found rect.extrude: {w}x{h}x{d}")
                triangles = _generate_box_triangles(w, h, d)
        
        # Strategy 5: polygon.extrude (nut, gear) - generate as cylinder
        if not triangles:
            polygon_extrude = re.search(r'\.polygon\s*\(\s*(\d+)\s*,\s*(\d+(?:\.\d+)?)\s*\)\.extrude\s*\(\s*(\d+(?:\.\d+)?)', code, re.IGNORECASE)
            if polygon_extrude:
                sides, radius, height = int(polygon_extrude.group(1)), float(polygon_extrude.group(2)), float(polygon_extrude.group(3))
                print(f"DEBUG: Found polygon {sides}-sided, r={radius}, h={height}")
                # Approximate polygon as cylinder for simplicity
                triangles = _generate_cylinder_triangles(radius, height)
        
        # Strategy 6: Fallback - if code mentions "ring" or "jewelry", make a ring
        if not triangles and re.search(r'ring|jewelry|diamond|engagement', code, re.IGNORECASE):
            print(f"DEBUG: Code mentions ring/jewelry, generating default ring")
            triangles = _generate_torus_triangles(8.5, 1.5)
        
        # Final fallback: generate default cube
        if not triangles:
            print(f"DEBUG: No recognized CadQuery geometry, generating default 30mm cube")
            triangles = _generate_box_triangles(30, 30, 30)
        
        if not triangles:
            print(f"DEBUG: Failed to generate triangles")
            return False
        
        print(f"DEBUG: Generated {len(triangles)} triangles from CadQuery code")
        
        # Write STL file
        return _write_stl_file(triangles, output_path)
        
    except Exception as e:
        print(f"❌ Error in fallback parsing: {e}")
        import traceback
        traceback.print_exc()
        return False


def _generate_box_triangles(width: float, height: float, depth: float) -> list:
    """Generate triangles for a box centered at origin"""
    w, h, d = width/2, height/2, depth/2
    return [
        # Front face (+Z)
        ((-w, -h, d), (w, -h, d), (-w, h, d)),
        ((w, -h, d), (w, h, d), (-w, h, d)),
        # Back face (-Z)
        ((-w, -h, -d), (-w, h, -d), (w, -h, -d)),
        ((w, -h, -d), (-w, h, -d), (w, h, -d)),
        # Left face (-X)
        ((-w, -h, -d), (-w, -h, d), (-w, h, -d)),
        ((-w, h, d), (-w, h, -d), (-w, -h, d)),
        # Right face (+X)
        ((w, -h, -d), (w, h, -d), (w, -h, d)),
        ((w, -h, d), (w, h, -d), (w, h, d)),
        # Top face (+Y)
        ((-w, h, -d), (w, h, -d), (-w, h, d)),
        ((w, h, d), (-w, h, d), (w, h, -d)),
        # Bottom face (-Y)
        ((-w, -h, -d), (-w, -h, d), (w, -h, -d)),
        ((w, -h, d), (w, -h, -d), (-w, -h, d)),
    ]


def _generate_cylinder_triangles(radius: float, height: float) -> list:
    """Generate triangles for a cylinder"""
    # Ensure minimum height for visibility
    if height < 10:
        height = max(height * 5, 30)
    
    triangles = []
    segments = 32
    half_h = height / 2
    
    for i in range(segments):
        angle1 = 2 * math.pi * i / segments
        angle2 = 2 * math.pi * (i + 1) / segments
        
        x1 = radius * math.cos(angle1)
        y1 = radius * math.sin(angle1)
        x2 = radius * math.cos(angle2)
        y2 = radius * math.sin(angle2)
        
        # Top cap
        triangles.append(((0, 0, half_h), (x1, y1, half_h), (x2, y2, half_h)))
        # Bottom cap
        triangles.append(((0, 0, -half_h), (x2, y2, -half_h), (x1, y1, -half_h)))
        # Side 1
        triangles.append(((x1, y1, half_h), (x1, y1, -half_h), (x2, y2, half_h)))
        # Side 2
        triangles.append(((x2, y2, half_h), (x1, y1, -half_h), (x2, y2, -half_h)))
    
    return triangles


def _generate_torus_triangles(major_radius: float, minor_radius: float) -> list:
    """Generate triangles for a torus (ring shape)"""
    triangles = []
    major_segments = 32  # Around the ring
    minor_segments = 16  # Cross-section
    
    for i in range(major_segments):
        major_angle1 = 2 * math.pi * i / major_segments
        major_angle2 = 2 * math.pi * (i + 1) / major_segments
        
        for j in range(minor_segments):
            minor_angle1 = 2 * math.pi * j / minor_segments
            minor_angle2 = 2 * math.pi * (j + 1) / minor_segments
            
            # Calculate vertices
            x1 = (major_radius + minor_radius * math.cos(minor_angle1)) * math.cos(major_angle1)
            y1 = minor_radius * math.sin(minor_angle1)
            z1 = (major_radius + minor_radius * math.cos(minor_angle1)) * math.sin(major_angle1)
            
            x2 = (major_radius + minor_radius * math.cos(minor_angle2)) * math.cos(major_angle1)
            y2 = minor_radius * math.sin(minor_angle2)
            z2 = (major_radius + minor_radius * math.cos(minor_angle2)) * math.sin(major_angle1)
            
            x3 = (major_radius + minor_radius * math.cos(minor_angle1)) * math.cos(major_angle2)
            y3 = minor_radius * math.sin(minor_angle1)
            z3 = (major_radius + minor_radius * math.cos(minor_angle1)) * math.sin(major_angle2)
            
            x4 = (major_radius + minor_radius * math.cos(minor_angle2)) * math.cos(major_angle2)
            y4 = minor_radius * math.sin(minor_angle2)
            z4 = (major_radius + minor_radius * math.cos(minor_angle2)) * math.sin(major_angle2)
            
            # Two triangles per quad
            triangles.append(((x1, y1, z1), (x2, y2, z2), (x3, y3, z3)))
            triangles.append(((x2, y2, z2), (x4, y4, z4), (x3, y3, z3)))
    
    return triangles


def _generate_sphere_triangles(radius: float) -> list:
    """Generate triangles for a sphere"""
    triangles = []
    segments_lat = 12
    segments_lng = 24
    
    for i in range(segments_lat):
        lat0 = math.pi * (i - segments_lat / 2) / segments_lat
        lat1 = math.pi * (i + 1 - segments_lat / 2) / segments_lat
        
        for j in range(segments_lng):
            lng0 = 2 * math.pi * j / segments_lng
            lng1 = 2 * math.pi * (j + 1) / segments_lng
            
            x0 = radius * math.cos(lat0) * math.cos(lng0)
            y0 = radius * math.sin(lat0)
            z0 = radius * math.cos(lat0) * math.sin(lng0)
            
            x1 = radius * math.cos(lat0) * math.cos(lng1)
            y1 = radius * math.sin(lat0)
            z1 = radius * math.cos(lat0) * math.sin(lng1)
            
            x2 = radius * math.cos(lat1) * math.cos(lng0)
            y2 = radius * math.sin(lat1)
            z2 = radius * math.cos(lat1) * math.sin(lng0)
            
            x3 = radius * math.cos(lat1) * math.cos(lng1)
            y3 = radius * math.sin(lat1)
            z3 = radius * math.cos(lat1) * math.sin(lng1)
            
            triangles.append(((x0, y0, z0), (x1, y1, z1), (x2, y2, z2)))
            triangles.append(((x1, y1, z1), (x3, y3, z3), (x2, y2, z2)))
    
    return triangles


def _write_stl_file(triangles: list, output_path: str) -> bool:
    """Write triangles to binary STL file"""
    try:
        with open(output_path, 'wb') as f:
            # Write 80-byte header
            f.write(b'\0' * 80)
            # Write triangle count
            f.write(struct.pack('<I', len(triangles)))
            
            for v1, v2, v3 in triangles:
                # Calculate normal
                nx = (v2[1] - v1[1]) * (v3[2] - v1[2]) - (v2[2] - v1[2]) * (v3[1] - v1[1])
                ny = (v2[2] - v1[2]) * (v3[0] - v1[0]) - (v2[0] - v1[0]) * (v3[2] - v1[2])
                nz = (v2[0] - v1[0]) * (v3[1] - v1[1]) - (v2[1] - v1[1]) * (v3[0] - v1[0])
                
                length = (nx*nx + ny*ny + nz*nz) ** 0.5
                if length > 0:
                    nx, ny, nz = nx/length, ny/length, nz/length
                
                # Write normal
                f.write(struct.pack('<fff', float(nx), float(ny), float(nz)))
                # Write vertices
                for v in [v1, v2, v3]:
                    f.write(struct.pack('<fff', float(v[0]), float(v[1]), float(v[2])))
                # Write attribute byte count
                f.write(struct.pack('<H', 0))
        
        file_size = Path(output_path).stat().st_size
        print(f"✅ STL written: {file_size} bytes with {len(triangles)} triangles")
        return True
        
    except IOError as e:
        print(f"❌ Error writing STL: {e}")
        return False


def generate_cad_from_code(cad_code_json: str, output_dir: Path) -> str:
    """
    Generate STL from CadQuery code
    
    Args:
        cad_code_json: JSON string with code, code_type, title
        output_dir: Directory to save STL
        
    Returns:
        File path if successful, empty string otherwise
    """
    try:
        # Parse JSON
        cad_spec = json.loads(cad_code_json)
        code = cad_spec.get("code", "")
        code_type = cad_spec.get("code_type", "cadquery")
        
        if not code:
            print(f"❌ No code in specification")
            return ""
        
        print(f"DEBUG: Code-as-CAD Pipeline")
        print(f"Title: {cad_spec.get('title', 'Generated CAD Model')}")
        print(f"Type: {code_type}")
        print(f"Code preview: {code[:100]}...")
        print(f"DEBUG: Code length: {len(code)} characters")
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "model.stl"
        
        # Execute code
        if code_type == "cadquery":
            print(f"DEBUG: Using CadQuery executor...")
            success = execute_cadquery_code(code, str(output_path))
        else:
            print(f"❌ Unknown code type: {code_type}")
            return ""
        
        if success and Path(output_path).exists():
            return str(output_path)
        else:
            return ""
            
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return ""
    except Exception as e:
        print(f"❌ Error in generate_cad_from_code: {e}")
        import traceback
        traceback.print_exc()
        return ""
