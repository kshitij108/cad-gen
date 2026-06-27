"""
mock_grasshopper_engine.py

Simulates Grasshopper template behavior locally without requiring Rhino Compute.
Generates valid STL geometry for testing the full CAD pipeline.

Used for:
1. Local development testing
2. CI/CD pipeline validation
3. Testing without Windows/Rhino access
4. Quality validation before real template deployment
"""

import struct
import math
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
from enum import Enum
import uuid
from datetime import datetime


class TemplateShape(Enum):
    """Supported template shapes"""
    CUBE = "cube"
    SPHERE = "sphere"
    CYLINDER = "cylinder"
    CONE = "cone"
    TORUS = "torus"
    WEDGE = "wedge"


@dataclass
class Vertex:
    """3D vertex"""
    x: float
    y: float
    z: float
    
    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)


@dataclass
class Normal:
    """Triangle normal vector"""
    x: float
    y: float
    z: float
    
    def to_bytes(self) -> bytes:
        return struct.pack('<fff', self.x, self.y, self.z)


@dataclass
class Triangle:
    """3D triangle (3 vertices + normal)"""
    normal: Normal
    v1: Vertex
    v2: Vertex
    v3: Vertex
    
    def to_binary(self) -> bytes:
        """Convert to binary STL triangle format"""
        data = self.normal.to_bytes()
        data += struct.pack('<fff', self.v1.x, self.v1.y, self.v1.z)
        data += struct.pack('<fff', self.v2.x, self.v2.y, self.v2.z)
        data += struct.pack('<fff', self.v3.x, self.v3.y, self.v3.z)
        data += struct.pack('<H', 0)  # Attribute byte count
        return data


class MockGrasshopper:
    """Mock Grasshopper engine for local testing"""
    
    def __init__(self):
        self.templates = {
            TemplateShape.CUBE: self._generate_cube,
            TemplateShape.SPHERE: self._generate_sphere,
            TemplateShape.CYLINDER: self._generate_cylinder,
            TemplateShape.CONE: self._generate_cone,
            TemplateShape.TORUS: self._generate_torus,
            TemplateShape.WEDGE: self._generate_wedge,
        }
    
    def generate(self, shape: TemplateShape, params: dict) -> List[Triangle]:
        """Generate triangles for given shape and parameters"""
        generator = self.templates.get(shape)
        if not generator:
            raise ValueError(f"Unknown shape: {shape}")
        return generator(params)
    
    def generate_to_stl(self, shape: TemplateShape, params: dict, output_path: str) -> dict:
        """Generate STL file and return metadata"""
        triangles = self.generate(shape, params)
        
        # Write binary STL
        with open(output_path, 'wb') as f:
            # Header (80 bytes)
            header = b'Mock Grasshopper STL export' + b' ' * (80 - 27)
            f.write(header)
            
            # Triangle count (4 bytes, little-endian)
            f.write(struct.pack('<I', len(triangles)))
            
            # Triangles
            for tri in triangles:
                f.write(tri.to_binary())
        
        # Calculate metadata
        file_size = Path(output_path).stat().st_size
        bounds = self._calculate_bounds(triangles)
        quality_score = self._calculate_quality(triangles, file_size, bounds)
        
        return {
            "file_path": output_path,
            "file_size_mb": file_size / (1024 * 1024),
            "triangle_count": len(triangles),
            "bounds": bounds,
            "quality_score": quality_score,
            "shape": shape.value,
            "parameters": params,
            "generated_at": datetime.now().isoformat()
        }
    
    # ============ Shape Generators ============
    
    def _generate_cube(self, params: dict) -> List[Triangle]:
        """Generate cube"""
        l = params.get('length', 100)
        w = params.get('width', 100)
        h = params.get('height', 100)
        
        # Vertices
        v = [
            Vertex(0, 0, 0),      # 0
            Vertex(l, 0, 0),      # 1
            Vertex(l, w, 0),      # 2
            Vertex(0, w, 0),      # 3
            Vertex(0, 0, h),      # 4
            Vertex(l, 0, h),      # 5
            Vertex(l, w, h),      # 6
            Vertex(0, w, h),      # 7
        ]
        
        triangles = []
        
        # Bottom (z=0)
        triangles.extend(self._create_quad_triangles(v[0], v[1], v[2], v[3], Normal(0, 0, -1)))
        
        # Top (z=h)
        triangles.extend(self._create_quad_triangles(v[4], v[7], v[6], v[5], Normal(0, 0, 1)))
        
        # Front (y=0)
        triangles.extend(self._create_quad_triangles(v[0], v[4], v[5], v[1], Normal(0, -1, 0)))
        
        # Back (y=w)
        triangles.extend(self._create_quad_triangles(v[2], v[6], v[7], v[3], Normal(0, 1, 0)))
        
        # Left (x=0)
        triangles.extend(self._create_quad_triangles(v[0], v[3], v[7], v[4], Normal(-1, 0, 0)))
        
        # Right (x=l)
        triangles.extend(self._create_quad_triangles(v[1], v[5], v[6], v[2], Normal(1, 0, 0)))
        
        return triangles
    
    def _generate_sphere(self, params: dict) -> List[Triangle]:
        """Generate sphere using icosphere algorithm"""
        radius = params.get('radius', 50)
        subdivisions = 2  # ~2560 triangles
        
        triangles = self._create_icosphere(radius, subdivisions)
        return triangles
    
    def _generate_cylinder(self, params: dict) -> List[Triangle]:
        """Generate cylinder"""
        radius = params.get('radius', 50)
        height = params.get('height', 100)
        segments = 24  # Number of sides
        
        triangles = []
        
        # Generate side vertices
        vertices = []
        for i in range(segments):
            angle = (2 * math.pi * i) / segments
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            
            # Bottom vertex
            vertices.append(Vertex(x, y, 0))
            # Top vertex
            vertices.append(Vertex(x, y, height))
        
        # Side faces
        for i in range(segments):
            next_i = (i + 1) % segments
            
            # Bottom-left, bottom-right, top-right, top-left
            v1 = vertices[i * 2]
            v2 = vertices[next_i * 2]
            v3 = vertices[next_i * 2 + 1]
            v4 = vertices[i * 2 + 1]
            
            triangles.extend(self._create_quad_triangles(v1, v2, v3, v4, Normal(0, 0, 0)))  # Normal calculated
        
        # Bottom cap
        center_bottom = Vertex(0, 0, 0)
        for i in range(segments):
            next_i = (i + 1) % segments
            v1 = vertices[i * 2]
            v2 = vertices[next_i * 2]
            tri = Triangle(Normal(0, 0, -1), center_bottom, v2, v1)
            triangles.append(tri)
        
        # Top cap
        center_top = Vertex(0, 0, height)
        for i in range(segments):
            next_i = (i + 1) % segments
            v1 = vertices[i * 2 + 1]
            v2 = vertices[next_i * 2 + 1]
            tri = Triangle(Normal(0, 0, 1), center_top, v1, v2)
            triangles.append(tri)
        
        return triangles
    
    def _generate_cone(self, params: dict) -> List[Triangle]:
        """Generate cone or truncated cone (frustum)"""
        radius = params.get('radius', 50)
        height = params.get('height', 100)
        tip_radius = params.get('tip_radius', 0)
        segments = 24
        
        triangles = []
        
        # Bottom circle vertices
        bottom_vertices = []
        for i in range(segments):
            angle = (2 * math.pi * i) / segments
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            bottom_vertices.append(Vertex(x, y, 0))
        
        # Top circle vertices (or point if tip_radius=0)
        top_vertices = []
        if tip_radius > 0:
            # Frustum (truncated cone)
            for i in range(segments):
                angle = (2 * math.pi * i) / segments
                x = tip_radius * math.cos(angle)
                y = tip_radius * math.sin(angle)
                top_vertices.append(Vertex(x, y, height))
        else:
            # True cone - apex point
            apex = Vertex(0, 0, height)
            top_vertices = [apex] * segments
        
        # Side faces
        for i in range(segments):
            next_i = (i + 1) % segments
            v1 = bottom_vertices[i]
            v2 = bottom_vertices[next_i]
            v3 = top_vertices[next_i]
            v4 = top_vertices[i]
            
            triangles.extend(self._create_quad_triangles(v1, v2, v3, v4, Normal(0, 0, 0)))
        
        # Bottom cap
        center_bottom = Vertex(0, 0, 0)
        for i in range(segments):
            next_i = (i + 1) % segments
            v1 = bottom_vertices[i]
            v2 = bottom_vertices[next_i]
            tri = Triangle(Normal(0, 0, -1), center_bottom, v2, v1)
            triangles.append(tri)
        
        # Top cap (only if frustum)
        if tip_radius > 0:
            center_top = Vertex(0, 0, height)
            for i in range(segments):
                next_i = (i + 1) % segments
                v1 = top_vertices[i]
                v2 = top_vertices[next_i]
                tri = Triangle(Normal(0, 0, 1), center_top, v1, v2)
                triangles.append(tri)
        
        return triangles
    
    def _generate_torus(self, params: dict) -> List[Triangle]:
        """Generate torus"""
        major_r = params.get('major_radius', 100)
        minor_r = params.get('minor_radius', 20)
        major_segments = 24
        minor_segments = 12
        
        triangles = []
        
        # Generate vertices for all rings and segments
        vertices = []
        for i in range(major_segments):
            ring = []
            major_angle = (2 * math.pi * i) / major_segments
            center_x = major_r * math.cos(major_angle)
            center_y = major_r * math.sin(major_angle)
            
            for j in range(minor_segments):
                minor_angle = (2 * math.pi * j) / minor_segments
                x = center_x + minor_r * math.cos(minor_angle) * math.cos(major_angle)
                y = center_y + minor_r * math.cos(minor_angle) * math.sin(major_angle)
                z = minor_r * math.sin(minor_angle)
                ring.append(Vertex(x, y, z))
            
            vertices.append(ring)
        
        # Create quads from rings
        for i in range(major_segments):
            next_i = (i + 1) % major_segments
            for j in range(minor_segments):
                next_j = (j + 1) % minor_segments
                
                v1 = vertices[i][j]
                v2 = vertices[next_i][j]
                v3 = vertices[next_i][next_j]
                v4 = vertices[i][next_j]
                
                triangles.extend(self._create_quad_triangles(v1, v2, v3, v4, Normal(0, 0, 0)))
        
        return triangles
    
    def _generate_wedge(self, params: dict) -> List[Triangle]:
        """Generate wedge (angled prism)"""
        base_l = params.get('base_length', 100)
        base_w = params.get('base_width', 100)
        height = params.get('height', 100)
        angle_deg = params.get('angle', 45)
        
        angle_rad = math.radians(angle_deg)
        horizontal_offset = height / math.tan(angle_rad)
        
        # Vertices
        v = [
            Vertex(0, 0, 0),                               # 0 - base front-left
            Vertex(base_l, 0, 0),                          # 1 - base front-right
            Vertex(base_l, base_w, 0),                     # 2 - base back-right
            Vertex(0, base_w, 0),                          # 3 - base back-left
            Vertex(horizontal_offset, 0, height),          # 4 - top front-left
            Vertex(base_l + horizontal_offset, 0, height), # 5 - top front-right
            Vertex(base_l + horizontal_offset, base_w, height), # 6 - top back-right
            Vertex(horizontal_offset, base_w, height),     # 7 - top back-left
        ]
        
        triangles = []
        
        # Bottom
        triangles.extend(self._create_quad_triangles(v[0], v[1], v[2], v[3], Normal(0, 0, -1)))
        
        # Top
        triangles.extend(self._create_quad_triangles(v[4], v[7], v[6], v[5], Normal(0, 0, 1)))
        
        # Front (sloped)
        triangles.extend(self._create_quad_triangles(v[0], v[4], v[5], v[1], Normal(0, 0, 0)))
        
        # Back
        triangles.extend(self._create_quad_triangles(v[2], v[6], v[7], v[3], Normal(0, 0, 0)))
        
        # Left (vertical)
        triangles.extend(self._create_quad_triangles(v[0], v[3], v[7], v[4], Normal(-1, 0, 0)))
        
        # Right (vertical)
        triangles.extend(self._create_quad_triangles(v[1], v[5], v[6], v[2], Normal(1, 0, 0)))
        
        return triangles
    
    # ============ Helper Methods ============
    
    def _create_quad_triangles(self, v1: Vertex, v2: Vertex, v3: Vertex, v4: Vertex, 
                               normal: Normal) -> List[Triangle]:
        """Create two triangles from quad"""
        # Auto-calculate normal if not provided
        if normal.x == 0 and normal.y == 0 and normal.z == 0:
            normal = self._calculate_normal(v1, v2, v3)
        
        return [
            Triangle(normal, v1, v2, v3),
            Triangle(normal, v1, v3, v4),
        ]
    
    def _calculate_normal(self, v1: Vertex, v2: Vertex, v3: Vertex) -> Normal:
        """Calculate surface normal from 3 vertices"""
        # Vectors
        u = (v2.x - v1.x, v2.y - v1.y, v2.z - v1.z)
        v = (v3.x - v1.x, v3.y - v1.y, v3.z - v1.z)
        
        # Cross product
        nx = u[1] * v[2] - u[2] * v[1]
        ny = u[2] * v[0] - u[0] * v[2]
        nz = u[0] * v[1] - u[1] * v[0]
        
        # Normalize
        length = math.sqrt(nx**2 + ny**2 + nz**2)
        if length > 0:
            nx /= length
            ny /= length
            nz /= length
        
        return Normal(nx, ny, nz)
    
    def _create_icosphere(self, radius: float, subdivisions: int) -> List[Triangle]:
        """Create icosphere"""
        t = (1 + math.sqrt(5)) / 2
        
        # Initial icosahedron vertices
        vertices = [
            (-1,  t, -1), ( 1,  t, -1), (-1,  t,  1), ( 1,  t,  1),
            (-1, -t, -1), ( 1, -t, -1), (-1, -t,  1), ( 1, -t,  1),
            (-t, -1, -1), ( t, -1, -1), (-t, -1,  1), ( t, -1,  1),
            (-t,  1, -1), ( t,  1, -1), (-t,  1,  1), ( t,  1,  1),
            (-1, -1, -t), ( 1, -1, -t), (-1, -1,  t), ( 1, -1,  t),
            (-1,  1, -t), ( 1,  1, -t), (-1,  1,  t), ( 1,  1,  t),
        ]
        
        # Triangles (faces)
        triangles_idx = [
            (0, 12, 16), (1, 15, 17), (0, 13, 12), (1, 14, 15),
            (2, 14, 22), (3, 15, 23), (2, 22, 11), (3, 23, 10),
        ]
        
        # Convert to Vertex objects and scale to radius
        v_objs = [Vertex(x * radius / 3, y * radius / 3, z * radius / 3) 
                  for x, y, z in vertices]
        
        triangles = []
        for i1, i2, i3 in triangles_idx:
            v1, v2, v3 = v_objs[i1], v_objs[i2], v_objs[i3]
            normal = self._calculate_normal(v1, v2, v3)
            triangles.append(Triangle(normal, v1, v2, v3))
        
        return triangles
    
    def _calculate_bounds(self, triangles: List[Triangle]) -> dict:
        """Calculate bounding box"""
        if not triangles:
            return {"min": {"x": 0, "y": 0, "z": 0}, "max": {"x": 0, "y": 0, "z": 0}}
        
        xs = []
        ys = []
        zs = []
        
        for tri in triangles:
            for v in [tri.v1, tri.v2, tri.v3]:
                xs.append(v.x)
                ys.append(v.y)
                zs.append(v.z)
        
        return {
            "min": {"x": min(xs), "y": min(ys), "z": min(zs)},
            "max": {"x": max(xs), "y": max(ys), "z": max(zs)},
        }
    
    def _calculate_quality(self, triangles: List[Triangle], file_size: int, bounds: dict) -> float:
        """Calculate quality score 0-100"""
        score = 100.0
        
        # Triangle count check
        if len(triangles) < 4:
            score -= 50
        elif len(triangles) > 5000000:
            score -= 10
        
        # File size check
        file_size_mb = file_size / (1024 * 1024)
        if file_size_mb > 100:
            score -= 10
        
        # Geometry check
        min_b = bounds["min"]
        max_b = bounds["max"]
        size_x = max_b["x"] - min_b["x"]
        size_y = max_b["y"] - min_b["y"]
        size_z = max_b["z"] - min_b["z"]
        
        # Check for degenerate geometry
        if size_x < 0.01 or size_y < 0.01 or size_z < 0.01:
            score -= 30
        
        return max(0, min(100, score))


def test_mock_grasshopper():
    """Test mock engine"""
    engine = MockGrasshopper()
    
    test_cases = [
        (TemplateShape.CUBE, {"length": 100, "width": 100, "height": 100}),
        (TemplateShape.SPHERE, {"radius": 50}),
        (TemplateShape.CYLINDER, {"radius": 50, "height": 100}),
        (TemplateShape.CONE, {"radius": 50, "height": 100}),
        (TemplateShape.TORUS, {"major_radius": 100, "minor_radius": 20}),
        (TemplateShape.WEDGE, {"base_length": 100, "base_width": 100, "height": 100, "angle": 45}),
    ]
    
    output_dir = Path("/tmp/mock_stl_test")
    output_dir.mkdir(exist_ok=True)
    
    results = []
    for shape, params in test_cases:
        output_file = output_dir / f"{shape.value}_test.stl"
        metadata = engine.generate_to_stl(shape, params, str(output_file))
        results.append(metadata)
        print(f"✓ {shape.value}: {metadata['triangle_count']} triangles, "
              f"{metadata['file_size_mb']:.2f}MB, quality={metadata['quality_score']}")
    
    return results


if __name__ == "__main__":
    # Run tests
    test_mock_grasshopper()
