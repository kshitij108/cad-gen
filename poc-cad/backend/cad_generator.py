"""
CAD file generation from specifications with shape detection
"""
import json
import os
from pathlib import Path
import struct
import math


def _write_stl_file(triangles: list, output_path: str) -> bool:
    """
    Write triangles to binary STL file format
    """
    try:
        with open(output_path, 'wb') as f:
            # 80 byte header
            f.write(b'\0' * 80)
            # Number of triangles
            f.write(struct.pack('<I', len(triangles)))
            
            # Write each triangle
            for tri in triangles:
                v1 = tri[0]
                v2 = tri[1]
                v3 = tri[2]
                
                # Calculate normal using cross product
                nx = (v2[1] - v1[1]) * (v3[2] - v1[2]) - (v2[2] - v1[2]) * (v3[1] - v1[1])
                ny = (v2[2] - v1[2]) * (v3[0] - v1[0]) - (v2[0] - v1[0]) * (v3[2] - v1[2])
                nz = (v2[0] - v1[0]) * (v3[1] - v1[1]) - (v2[1] - v1[1]) * (v3[0] - v1[0])
                
                # Normalize
                length = (nx*nx + ny*ny + nz*nz) ** 0.5
                if length > 0:
                    nx, ny, nz = nx/length, ny/length, nz/length
                
                # Write normal vector
                f.write(struct.pack('<fff', float(nx), float(ny), float(nz)))
                
                # Write vertices
                for v in tri:
                    f.write(struct.pack('<fff', float(v[0]), float(v[1]), float(v[2])))
                
                # Attribute byte count
                f.write(struct.pack('<H', 0))
        
        return True
    except Exception as e:
        print(f"Error writing STL file: {e}")
        return False


def create_cube_stl(dimensions, return_triangles: bool = False):
    """Create a cube STL
    
    Args:
        dimensions: [width, height, depth] in mm
        return_triangles: If True, return triangle list; if False, write to file
    """
    try:
        w, h, d = dimensions[0], dimensions[1], dimensions[2] if len(dimensions) > 2 else dimensions[0]
        w, h, d = w/2, h/2, d/2
        
        triangles = [
            # Front face
            ((-w, -h, d), (w, -h, d), (-w, h, d)),
            ((w, -h, d), (w, h, d), (-w, h, d)),
            # Back face
            ((-w, -h, -d), (-w, h, -d), (w, -h, -d)),
            ((w, -h, -d), (-w, h, -d), (w, h, -d)),
            # Left face
            ((-w, -h, -d), (-w, -h, d), (-w, h, -d)),
            ((-w, h, d), (-w, h, -d), (-w, -h, d)),
            # Right face
            ((w, -h, -d), (w, h, -d), (w, -h, d)),
            ((w, -h, d), (w, h, -d), (w, h, d)),
            # Top face
            ((-w, h, -d), (w, h, -d), (-w, h, d)),
            ((w, h, d), (-w, h, d), (w, h, -d)),
            # Bottom face
            ((-w, -h, -d), (-w, -h, d), (w, -h, -d)),
            ((w, -h, d), (w, -h, -d), (-w, -h, d)),
        ]
        
        if return_triangles:
            return triangles
        return triangles
        
    except Exception as e:
        print(f"Error creating cube: {e}")
        return [] if return_triangles else False


def create_cylinder_stl(radius: float, height: float, output_path: str = None, segments: int = 16, return_triangles: bool = False):
    """Create a cylindrical STL file"""
    try:
        triangles = []
        half_height = height / 2
        
        # Generate points around the cylinder
        for i in range(segments):
            angle1 = 2 * math.pi * i / segments
            angle2 = 2 * math.pi * (i + 1) / segments
            
            x1 = radius * math.cos(angle1)
            y1 = radius * math.sin(angle1)
            x2 = radius * math.cos(angle2)
            y2 = radius * math.sin(angle2)
            
            # Top circle triangles
            triangles.append(((0, 0, half_height), (x1, y1, half_height), (x2, y2, half_height)))
            
            # Bottom circle triangles
            triangles.append(((0, 0, -half_height), (x2, y2, -half_height), (x1, y1, -half_height)))
            
            # Side triangles (2 per segment)
            triangles.append(((x1, y1, half_height), (x1, y1, -half_height), (x2, y2, half_height)))
            triangles.append(((x2, y2, half_height), (x1, y1, -half_height), (x2, y2, -half_height)))
        
        if return_triangles:
            return triangles
        
        return _write_stl_file(triangles, output_path) if output_path else True
    except Exception as e:
        print(f"Error creating cylinder STL: {e}")
        return [] if return_triangles else False


def create_sphere_stl(radius: float, output_path: str = None, segments: int = 8, return_triangles: bool = False):
    """Create a spherical STL file"""
    try:
        triangles = []
        
        for i in range(segments):
            lat0 = math.pi * (i - segments / 2) / segments
            lat1 = math.pi * (i + 1 - segments / 2) / segments
            
            for j in range(segments * 2):
                lng0 = 2 * math.pi * (j) / (segments * 2)
                lng1 = 2 * math.pi * (j + 1) / (segments * 2)
                
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
        
        if return_triangles:
            return triangles
        
        return _write_stl_file(triangles, output_path) if output_path else True
    except Exception as e:
        print(f"Error creating sphere STL: {e}")
        return [] if return_triangles else False


def create_cone_stl(radius: float, height: float, output_path: str = None, segments: int = 16, return_triangles: bool = False):
    """Create a conical STL file"""
    try:
        triangles = []
        apex = (0, 0, height / 2)
        base_z = -height / 2
        
        for i in range(segments):
            angle1 = 2 * math.pi * i / segments
            angle2 = 2 * math.pi * (i + 1) / segments
            
            x1 = radius * math.cos(angle1)
            y1 = radius * math.sin(angle1)
            x2 = radius * math.cos(angle2)
            y2 = radius * math.sin(angle2)
            
            # Side triangles
            triangles.append((apex, (x1, y1, base_z), (x2, y2, base_z)))
            
            # Base triangles
            triangles.append(((0, 0, base_z), (x2, y2, base_z), (x1, y1, base_z)))
        
        if return_triangles:
            return triangles
        
        return _write_stl_file(triangles, output_path) if output_path else True
    except Exception as e:
        print(f"Error creating cone STL: {e}")
        return [] if return_triangles else False


def create_torus_stl(major_radius: float, minor_radius: float, output_path: str, major_segments: int = 20, minor_segments: int = 12) -> bool:
    """Create a torus (donut/ring) STL file
    
    Args:
        major_radius: Distance from center to middle of tube
        minor_radius: Radius of tube cross-section
        output_path: Where to save
        major_segments: Segments around the main circle (higher = smoother ring)
        minor_segments: Segments around the tube (lower = flatter band)
    """
    try:
        triangles = []
        
        for i in range(major_segments):
            u1 = 2 * math.pi * i / major_segments
            u2 = 2 * math.pi * (i + 1) / major_segments
            
            for j in range(minor_segments):
                v1 = 2 * math.pi * j / minor_segments
                v2 = 2 * math.pi * (j + 1) / minor_segments
                
                # Calculate vertices on the torus
                x1 = (major_radius + minor_radius * math.cos(v1)) * math.cos(u1)
                y1 = (major_radius + minor_radius * math.cos(v1)) * math.sin(u1)
                z1 = minor_radius * math.sin(v1)
                
                x2 = (major_radius + minor_radius * math.cos(v2)) * math.cos(u1)
                y2 = (major_radius + minor_radius * math.cos(v2)) * math.sin(u1)
                z2 = minor_radius * math.sin(v2)
                
                x3 = (major_radius + minor_radius * math.cos(v1)) * math.cos(u2)
                y3 = (major_radius + minor_radius * math.cos(v1)) * math.sin(u2)
                z3 = minor_radius * math.sin(v1)
                
                x4 = (major_radius + minor_radius * math.cos(v2)) * math.cos(u2)
                y4 = (major_radius + minor_radius * math.cos(v2)) * math.sin(u2)
                z4 = minor_radius * math.sin(v2)
                
                # Two triangles per quad
                triangles.append(((x1, y1, z1), (x2, y2, z2), (x3, y3, z3)))
                triangles.append(((x2, y2, z2), (x4, y4, z4), (x3, y3, z3)))
        
        return _write_stl_file(triangles, output_path)
    except Exception as e:
        print(f"Error creating torus STL: {e}")
        return False


def create_complex_placeholder_stl(title: str, output_path: str) -> bool:
    """Create a placeholder mesh for complex geometries (jewelry, decorative items)"""
    try:
        # For complex items, create a simple icosahedron (20 faces) as placeholder
        # This allows the file to be valid while indicating detailed geometry is needed
        phi = (1 + 5**0.5) / 2
        vertices = [
            (-1,  phi, -0),
            (1,  phi,  0),
            (-1, -phi,  0),
            (1, -phi,  0),
            (0, -1,  phi),
            (0,  1,  phi),
            (0, -1, -phi),
            (0,  1, -phi),
            (phi, -0, -1),
            (phi,  0,  1),
            (-phi, -0, -1),
            (-phi,  0,  1),
        ]
        
        # Scale to reasonable size
        scale = 10
        vertices = [(v[0]*scale, v[1]*scale, v[2]*scale) for v in vertices]
        
        # Icosahedron faces (20 triangles)
        faces = [
            (0, 11, 5),
            (0, 5, 1),
            (0, 1, 7),
            (0, 7, 10),
            (0, 10, 11),
            (1, 5, 9),
            (5, 11, 4),
            (11, 10, 2),
            (10, 7, 6),
            (7, 1, 8),
            (3, 9, 4),
            (3, 4, 2),
            (3, 2, 6),
            (3, 6, 8),
            (3, 8, 9),
            (4, 9, 5),
            (2, 4, 11),
            (6, 2, 10),
            (8, 6, 7),
            (9, 8, 1),
        ]
        
        triangles = [(vertices[f[0]], vertices[f[1]], vertices[f[2]]) for f in faces]
        success = _write_stl_file(triangles, output_path)
        
        if success:
            print(f"⚠️  Complex geometry '{title}' - created placeholder icosahedron")
            print(f"    NOTE: For detailed jewelry/decorative items, use CAD software or provide CAD file")
        
        return success
    except Exception as e:
        print(f"Error creating complex placeholder: {e}")
        return False


def create_box_stl(dimensions: dict, output_path: str) -> bool:
    """Create a simple box/rectangular STL file"""
    try:
        w = dimensions.get("width", 10) / 2
        h = dimensions.get("height", 10) / 2
        d = dimensions.get("depth", 10) / 2
        
        # Define vertices for a box
        vertices = [
            (-w, -h, -d), (w, -h, -d), (w, h, -d), (-w, h, -d),  # bottom
            (-w, -h, d), (w, -h, d), (w, h, d), (-w, h, d),  # top
        ]
        
        # Define triangles (2 per face, 6 faces = 12 triangles)
        triangles = [
            # Bottom face
            (vertices[0], vertices[1], vertices[2]),
            (vertices[0], vertices[2], vertices[3]),
            # Top face
            (vertices[4], vertices[6], vertices[5]),
            (vertices[4], vertices[7], vertices[6]),
            # Front face
            (vertices[0], vertices[5], vertices[1]),
            (vertices[0], vertices[4], vertices[5]),
            # Back face
            (vertices[2], vertices[7], vertices[3]),
            (vertices[2], vertices[6], vertices[7]),
            # Left face
            (vertices[0], vertices[3], vertices[7]),
            (vertices[0], vertices[7], vertices[4]),
            # Right face
            (vertices[1], vertices[5], vertices[6]),
            (vertices[1], vertices[6], vertices[2]),
        ]
        
        return _write_stl_file(triangles, output_path)
    except Exception as e:
        print(f"Error creating box STL: {e}")
        return False


def detect_shape_type(cad_spec: dict) -> str:
    """
    Detect the shape type from Claude's CAD specification
    
    Returns: 'cylinder', 'sphere', 'cone', 'torus', 'box', or 'complex'
    """
    title = (cad_spec.get("title", "") or "").lower()
    description = (cad_spec.get("description", "") or "").lower()
    features = [f.lower() for f in (cad_spec.get("features") or [])]
    complexity = (cad_spec.get("complexity", "simple") or "simple").lower()
    
    # Combine all text to search
    all_text = f"{title} {description} {' '.join(features)}"
    
    # SPECIAL CASE: Jewelry rings (engagement ring, wedding ring, etc.) → TORUS
    # Check for ring + jewelry indicators BEFORE other shape detection
    jewelry_ring_keywords = [
        "engagement ring", "wedding ring", "band", "diamond ring", 
        "gemstone ring", "solitaire ring", "eternity ring"
    ]
    if any(phrase in all_text for phrase in jewelry_ring_keywords):
        return "torus"
    
    # CHECK SPECIFIC GEOMETRIC SHAPES
    if any(word in all_text for word in ["cylinder", "shaft", "rod", "pipe", "tube", "circular cross"]):
        return "cylinder"
    elif any(word in all_text for word in ["sphere", "ball", "spherical", "bearing", "globe"]):
        return "sphere"
    elif any(word in all_text for word in ["cone", "conical", "tapered", "funnel"]):
        return "cone"
    elif any(word in all_text for word in ["torus", "donut", "ring", "circular loop", "band", "round loop"]):
        return "torus"
    elif any(word in all_text for word in ["box", "cube", "rectangular", "block", "rectangular box"]):
        return "box"
    
    # Check for complex/decorative items (only if no specific shape matched)
    complex_keywords = [
        "jewelry", "decorative", "ornamental", "custom", "detailed",
        "diamond", "gem", "intricate", "carved", "sculpted", "artistic",
        "pendant", "bracelet", "necklace", "tiara", "crown"
    ]
    
    if any(word in all_text for word in complex_keywords) or complexity in ["complex", "detailed", "intricate"]:
        return "complex"
    
    return "box"  # Default to box


def generate_cad_file(cad_spec_json: str, output_dir: Path, file_format: str = "STL") -> str:
    """
    Generate CAD file in STL format with shape detection
    
    Args:
        cad_spec_json: JSON specification from Claude
        output_dir: Directory to save the file
        file_format: File format (STEP or STL) - both generate STL for compatibility
        
    Returns:
        File path if successful, empty string otherwise
    """
    try:
        spec = json.loads(cad_spec_json)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Detect shape type from specification
        shape_type = detect_shape_type(spec)
        dims = spec.get("dimensions", {})
        title = spec.get("title", "Model")
        
        file_path = output_dir / "model.stl"
        
        print(f"DEBUG: Detected shape type: {shape_type}")
        print(f"DEBUG: Title: {title}")
        print(f"DEBUG: Dimensions: {dims}")
        
        # Generate appropriate geometry based on shape type
        if shape_type == "complex":
            # Complex/decorative geometry (jewelry, ornaments, etc.)
            print(f"DEBUG: Creating complex geometry placeholder")
            success = create_complex_placeholder_stl(title, str(file_path))
            
        elif shape_type == "cylinder":
            # For cylinders: width/height = diameter, depth = length
            diameter = dims.get("width", 20)
            radius = diameter / 2
            height = dims.get("depth", 50)
            print(f"DEBUG: Creating cylinder with radius={radius}, height={height}")
            success = create_cylinder_stl(radius, height, str(file_path))
            
        elif shape_type == "sphere":
            # For spheres: width = diameter
            diameter = dims.get("width", 20)
            radius = diameter / 2
            print(f"DEBUG: Creating sphere with radius={radius}")
            success = create_sphere_stl(radius, str(file_path))
            
        elif shape_type == "cone":
            # For cones: width = base diameter, depth = height
            diameter = dims.get("width", 20)
            radius = diameter / 2
            height = dims.get("depth", 30)
            print(f"DEBUG: Creating cone with radius={radius}, height={height}")
            success = create_cone_stl(radius, height, str(file_path))
            
        elif shape_type == "torus":
            # For torus (rings): Create a slim band like a real ring
            # width/height = band dimensions, depth = outer diameter
            # For engagement rings, use smaller proportions for a delicate band
            
            outer_diameter = max(dims.get("depth", 20), dims.get("width", 20))
            band_thickness = min(dims.get("height", 2), dims.get("width", 2))
            
            # Ensure band thickness is realistic (1.5-3mm for jewelry)
            # Scale down if dimensions suggest thicker ring
            if band_thickness > 5:
                band_thickness = 2.5  # Realistic jewelry band
            elif band_thickness < 0.5:
                band_thickness = 1.5
            
            # Calculate torus radii for slim ring
            major_radius = (outer_diameter - band_thickness) / 2
            minor_radius = band_thickness / 2
            
            # Safety check: ensure valid geometry
            if major_radius < minor_radius * 1.5:
                # If ring is too small/thick, scale proportionally
                major_radius = max(6, outer_diameter / 3)
                minor_radius = max(0.75, major_radius / 6)
            
            print(f"DEBUG: Creating slim ring torus with major_radius={major_radius}, minor_radius={minor_radius}")
            success = create_torus_stl(major_radius, minor_radius, str(file_path), major_segments=24, minor_segments=8)
            
        else:  # box or unknown
            print(f"DEBUG: Creating box with dimensions={dims}")
            success = create_box_stl(dims, str(file_path))
        
        return str(file_path) if success else ""
        
    except Exception as e:
        print(f"Error in generate_cad_file: {e}")
        import traceback
        traceback.print_exc()
        return ""
