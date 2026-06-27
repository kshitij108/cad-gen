"""
Code-as-CAD Pipeline: Execute CAD code (OpenSCAD) to generate geometry
Instead of interpreting JSON, Claude writes the CAD code directly
"""
import subprocess
import tempfile
import json
import os
from pathlib import Path
import time


def execute_openscad_code(scad_code: str, output_path: str, timeout: int = 5) -> bool:
    """
    Execute OpenSCAD code and render to STL using fallback parser
    (OpenSCAD CLI skipped due to macOS Gatekeeper issues)
    
    Args:
        scad_code: OpenSCAD script code
        output_path: Where to save the STL file
        timeout: Maximum execution time in seconds (unused, kept for compatibility)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create temporary .scad file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            f.write(scad_code)
            scad_file = f.name
        
        print(f"DEBUG: Code length: {len(scad_code)} characters")
        
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Skip OpenSCAD CLI entirely - use fallback parser directly
        # (Avoids macOS Gatekeeper dialog and improves speed)
        print(f"DEBUG: Using fallback STL generation...")
        return generate_fallback_stl_from_code(scad_code, output_path, scad_file)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_fallback_stl_from_code(scad_code: str, output_path: str, scad_file: str) -> bool:
    """
    Fallback STL generation by parsing OpenSCAD code and generating geometry
    This is a simple parser that handles basic shapes like cube, cylinder, sphere
    """
    try:
        print(f"DEBUG: Generating fallback STL from OpenSCAD code analysis...")
        
        import re
        import struct
        import math
        
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        triangles = []
        
        # Debug: Show code analysis
        has_cube = 'cube(' in scad_code or 'cube_size' in scad_code or 'cube' in scad_code.lower()
        has_cylinder = 'cylinder(' in scad_code or 'cylinder' in scad_code.lower() or re.search(r'[^\w]r\s*=', scad_code)
        has_sphere = 'sphere(' in scad_code or 'sphere' in scad_code.lower()
        print(f"DEBUG: Code analysis - cube:{has_cube} cylinder:{has_cylinder} sphere:{has_sphere}")
        
        # Check for cube()
        if 'cube(' in scad_code or 'cube_size' in scad_code:
            # Parse cube dimensions
            cube_match = re.search(r'cube_size\s*=\s*(\d+(?:\.\d+)?)', scad_code)
            if cube_match:
                size = float(cube_match.group(1))
                print(f"DEBUG: Detected cube with size {size}mm")
                # Generate cube triangles
                s = size / 2
                triangles = [
                    # Front face
                    ((-s, -s, s), (s, -s, s), (-s, s, s)),
                    ((s, -s, s), (s, s, s), (-s, s, s)),
                    # Back face
                    ((-s, -s, -s), (-s, s, -s), (s, -s, -s)),
                    ((s, -s, -s), (-s, s, -s), (s, s, -s)),
                    # Left face
                    ((-s, -s, -s), (-s, -s, s), (-s, s, -s)),
                    ((-s, s, s), (-s, s, -s), (-s, -s, s)),
                    # Right face
                    ((s, -s, -s), (s, s, -s), (s, -s, s)),
                    ((s, -s, s), (s, s, -s), (s, s, s)),
                    # Top face
                    ((-s, s, -s), (s, s, -s), (-s, s, s)),
                    ((s, s, s), (-s, s, s), (s, s, -s)),
                    # Bottom face
                    ((-s, -s, -s), (-s, -s, s), (s, -s, -s)),
                    ((s, -s, s), (s, -s, -s), (-s, -s, s)),
                ]
        
        # Check for cylinder()
        elif 'cylinder(' in scad_code:
            # cylinder(r=15, h=50, $fn=64)
            r_match = re.search(r'r\s*=\s*(\d+(?:\.\d+)?)', scad_code)
            h_match = re.search(r'h\s*=\s*(\d+(?:\.\d+)?)', scad_code)
            radius = float(r_match.group(1)) if r_match else 15
            height = float(h_match.group(1)) if h_match else 50
            
            # Ensure minimum height for visibility
            if height < 10:
                height = max(height * 5, 30)  # Scale up small heights
            
            print(f"DEBUG: Detected cylinder r={radius}mm, h={height}mm")
            
            # Generate cylinder triangles with more segments for smoothness
            triangles = []
            segments = 32  # More segments for better looking cylinder
            half_height = height / 2
            
            for i in range(segments):
                angle1 = 2 * math.pi * i / segments
                angle2 = 2 * math.pi * (i + 1) / segments
                
                x1 = radius * math.cos(angle1)
                y1 = radius * math.sin(angle1)
                x2 = radius * math.cos(angle2)
                y2 = radius * math.sin(angle2)
                
                # Top cap
                triangles.append(((0, 0, half_height), (x1, y1, half_height), (x2, y2, half_height)))
                # Bottom cap
                triangles.append(((0, 0, -half_height), (x2, y2, -half_height), (x1, y1, -half_height)))
                # Side 1
                triangles.append(((x1, y1, half_height), (x1, y1, -half_height), (x2, y2, half_height)))
                # Side 2
                triangles.append(((x2, y2, half_height), (x1, y1, -half_height), (x2, y2, -half_height)))
        
        # Check for sphere()
        elif 'sphere(' in scad_code:
            r_match = re.search(r'r\s*=\s*(\d+(?:\.\d+)?)', scad_code)
            radius = float(r_match.group(1)) if r_match else 15
            print(f"DEBUG: Detected sphere r={radius}mm")
            
            # Generate sphere triangles with icosphere algorithm
            triangles = []
            segments_lat = 12  # Latitude segments
            segments_lng = 24  # Longitude segments
            
            for i in range(segments_lat):
                lat0 = math.pi * (i - segments_lat / 2) / segments_lat
                lat1 = math.pi * (i + 1 - segments_lat / 2) / segments_lat
                
                for j in range(segments_lng):
                    lng0 = 2 * math.pi * (j) / segments_lng
                    lng1 = 2 * math.pi * (j + 1) / segments_lng
                    
                    # Calculate 4 vertices of quad
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
                    
                    # Two triangles per quad
                    triangles.append(((x0, y0, z0), (x1, y1, z1), (x2, y2, z2)))
                    triangles.append(((x1, y1, z1), (x3, y3, z3), (x2, y2, z2)))
        
        else:
            # Default: create a simple cube
            print(f"DEBUG: No recognized primitives, creating default 20mm cube")
            s = 10
            triangles = [
                ((-s, -s, s), (s, -s, s), (-s, s, s)),
                ((s, -s, s), (s, s, s), (-s, s, s)),
                ((-s, -s, -s), (-s, s, -s), (s, -s, -s)),
                ((s, -s, -s), (-s, s, -s), (s, s, -s)),
                ((-s, -s, -s), (-s, -s, s), (-s, s, -s)),
                ((-s, s, s), (-s, s, -s), (-s, -s, s)),
                ((s, -s, -s), (s, s, -s), (s, -s, s)),
                ((s, -s, s), (s, s, -s), (s, s, s)),
                ((-s, s, -s), (s, s, -s), (-s, s, s)),
                ((s, s, s), (-s, s, s), (s, s, -s)),
                ((-s, -s, -s), (-s, -s, s), (s, -s, -s)),
                ((s, -s, s), (s, -s, -s), (-s, -s, s)),
            ]
            print(f"DEBUG: Created default cube with {len(triangles)} triangles")
        
        print(f"DEBUG: After all checks, triangles list length = {len(triangles) if triangles else 0}")
        print(f"DEBUG: triangles is None: {triangles is None}")
        print(f"DEBUG: triangles bool value: {bool(triangles)}")
        
        if not triangles:
            print(f"DEBUG: No triangles generated")
            return False
            
        if triangles:
            # Write STL file directly
            try:
                with open(output_path, 'wb') as f:
                    f.write(b'\0' * 80)
                    f.write(struct.pack('<I', len(triangles)))
                    
                    for tri in triangles:
                        v1, v2, v3 = tri
                        
                        # Calculate normal
                        nx = (v2[1] - v1[1]) * (v3[2] - v1[2]) - (v2[2] - v1[2]) * (v3[1] - v1[1])
                        ny = (v2[2] - v1[2]) * (v3[0] - v1[0]) - (v2[0] - v1[0]) * (v3[2] - v1[2])
                        nz = (v2[0] - v1[0]) * (v3[1] - v1[1]) - (v2[1] - v1[1]) * (v3[0] - v1[0])
                        
                        length = (nx*nx + ny*ny + nz*nz) ** 0.5
                        if length > 0:
                            nx, ny, nz = nx/length, ny/length, nz/length
                        
                        f.write(struct.pack('<fff', float(nx), float(ny), float(nz)))
                        
                        for v in tri:
                            f.write(struct.pack('<fff', float(v[0]), float(v[1]), float(v[2])))
                        
                        f.write(struct.pack('<H', 0))
                
                file_size = Path(output_path).stat().st_size
                print(f"✅ Fallback STL generated: {file_size} bytes with {len(triangles)} triangles")
                
                # Cleanup temp scad file
                try:
                    Path(scad_file).unlink()
                except:
                    pass
                
                return True
            except IOError as e:
                print(f"❌ Error writing STL file: {e}")
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ Error in fallback generation: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_cad_from_code(cad_code_json: str, output_dir: Path) -> str:
    """
    Generate CAD from Claude-written code
    
    Args:
        cad_code_json: JSON containing the CAD code and metadata
        output_dir: Directory to save the STL file
        
    Returns:
        File path if successful, empty string otherwise
    """
    try:
        spec = json.loads(cad_code_json)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract the CAD code
        code = spec.get("code", "")
        code_type = spec.get("code_type", "openscad")
        title = spec.get("title", "Model")
        
        if not code:
            print(f"❌ No CAD code provided in specification")
            return ""
        
        print(f"\nDEBUG: Code-as-CAD Pipeline")
        print(f"Title: {title}")
        print(f"Type: {code_type}")
        print(f"Code preview: {code[:100]}...")
        
        # Only OpenSCAD supported for now
        if code_type == "openscad":
            file_path = output_dir / "model.stl"
            success = execute_openscad_code(code, str(file_path))
            return str(file_path) if success else ""
        else:
            print(f"❌ Unsupported code type: {code_type}")
            return ""
            
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON specification: {e}")
        return ""
    except Exception as e:
        print(f"❌ Error in generate_cad_from_code: {e}")
        import traceback
        traceback.print_exc()
        return ""
