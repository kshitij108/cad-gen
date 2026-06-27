"""
Export Manager
Convert generated STL to multiple formats (STEP, OBJ, etc)
"""

import json
from pathlib import Path
from typing import Dict, Optional
from enum import Enum
import struct
import re


class ExportFormat(str, Enum):
    """Supported export formats"""
    STL_ASCII = "stl_ascii"
    STL_BINARY = "stl_binary"
    OBJ = "obj"
    STEP = "step"
    IGES = "iges"
    VRML = "vrml"


class ExportQuality(str, Enum):
    """Export quality levels"""
    DRAFT = "draft"           # Lower polygon count
    NORMAL = "normal"         # Standard
    PRODUCTION = "production" # High quality


class ExportManager:
    """Manages format conversions and exports"""
    
    def __init__(self, output_dir: Path = Path("./cad_models")):
        self.output_dir = output_dir
    
    def get_export_formats(self) -> Dict:
        """Get supported export formats with metadata"""
        return {
            "formats": [
                {
                    "format": "stl_binary",
                    "name": "STL Binary",
                    "extension": ".stl",
                    "description": "Standard binary STL format for 3D printing",
                    "suitable_for": ["3D printing", "CAM", "simulation"],
                    "file_size_estimate": "1.5x original"
                },
                {
                    "format": "stl_ascii",
                    "name": "STL ASCII",
                    "extension": ".stl",
                    "description": "Human-readable STL format",
                    "suitable_for": ["debugging", "inspection", "documentation"],
                    "file_size_estimate": "2-3x original"
                },
                {
                    "format": "obj",
                    "name": "Wavefront OBJ",
                    "extension": ".obj",
                    "description": "Mesh format for 3D graphics and visualization",
                    "suitable_for": ["3D visualization", "graphics", "animation"],
                    "file_size_estimate": "1-2x original",
                    "quality_levels": ["draft", "normal", "production"]
                },
                {
                    "format": "step",
                    "name": "STEP (CAD)",
                    "extension": ".step",
                    "description": "ISO standard for CAD data exchange",
                    "suitable_for": ["CAD software", "engineering", "manufacturing"],
                    "requires": "Rhino Compute integration",
                    "status": "requires_rhino"
                },
                {
                    "format": "iges",
                    "name": "IGES (CAD)",
                    "extension": ".iges",
                    "description": "Industry standard CAD format",
                    "suitable_for": ["CAD software", "legacy systems"],
                    "requires": "Rhino Compute integration",
                    "status": "requires_rhino"
                },
                {
                    "format": "vrml",
                    "name": "VRML",
                    "extension": ".wrl",
                    "description": "Virtual Reality Markup Language",
                    "suitable_for": ["web visualization", "virtual environments"],
                    "status": "planned"
                }
            ]
        }
    
    async def export(
        self,
        job_id: str,
        format: str,
        quality: str = "normal"
    ) -> Dict:
        """
        Export model to specified format
        
        Args:
            job_id: Job ID of model to export
            format: Export format (see ExportFormat enum)
            quality: Quality level for formats that support it
            
        Returns:
            Export result with file path
        """
        try:
            # Validate format
            if format not in [f.value for f in ExportFormat]:
                return {
                    "status": "error",
                    "error": f"Unsupported format: {format}"
                }
            
            # Check if job exists
            job_dir = self.output_dir / job_id
            stl_file = job_dir / "model.stl"
            
            if not stl_file.exists():
                return {
                    "status": "error",
                    "error": "Model not found"
                }
            
            # Determine output filename
            output_filename = self._get_output_filename(job_id, format)
            output_path = job_dir / output_filename
            
            # Perform conversion
            if format == "stl_ascii":
                result = self._convert_to_ascii_stl(stl_file, output_path)
            elif format == "stl_binary":
                result = self._ensure_binary_stl(stl_file, output_path)
            elif format == "obj":
                result = await self._convert_to_obj(stl_file, output_path, quality)
            elif format == "step":
                result = await self._convert_to_step(job_id, output_path)
            elif format == "iges":
                result = await self._convert_to_iges(job_id, output_path)
            else:
                return {
                    "status": "error",
                    "error": f"Format {format} not yet implemented"
                }
            
            return result
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _get_output_filename(self, job_id: str, format: str) -> str:
        """Get output filename based on format"""
        extensions = {
            "stl_ascii": ".stl",
            "stl_binary": ".stl",
            "obj": ".obj",
            "step": ".step",
            "iges": ".iges",
            "vrml": ".wrl"
        }
        
        extension = extensions.get(format, ".model")
        return f"model_{format}{extension}"
    
    def _convert_to_ascii_stl(self, input_file: Path, output_file: Path) -> Dict:
        """Convert STL to ASCII format"""
        try:
            # Read binary or ASCII STL
            with open(input_file, 'rb') as f:
                header = f.read(5)
            
            if header == b"solid":
                # Already ASCII
                output_file.write_text(input_file.read_text())
                return {
                    "status": "success",
                    "format": "stl_ascii",
                    "file_path": str(output_file),
                    "file_size_mb": output_file.stat().st_size / (1024 * 1024)
                }
            
            # Convert binary to ASCII
            vertices = self._parse_binary_stl_vertices(input_file)
            ascii_content = self._generate_ascii_stl(vertices)
            
            output_file.write_text(ascii_content)
            
            return {
                "status": "success",
                "format": "stl_ascii",
                "file_path": str(output_file),
                "file_size_mb": output_file.stat().st_size / (1024 * 1024),
                "vertex_count": len(vertices)
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _ensure_binary_stl(self, input_file: Path, output_file: Path) -> Dict:
        """Ensure STL is in binary format"""
        try:
            with open(input_file, 'rb') as f:
                header = f.read(5)
            
            if header != b"solid":
                # Already binary
                input_file.read_bytes()  # Verify readable
                output_file.write_bytes(input_file.read_bytes())
                return {
                    "status": "success",
                    "format": "stl_binary",
                    "file_path": str(output_file),
                    "file_size_mb": output_file.stat().st_size / (1024 * 1024)
                }
            
            # Convert ASCII to binary
            vertices = self._parse_ascii_stl_vertices(input_file)
            binary_content = self._generate_binary_stl(vertices)
            
            output_file.write_bytes(binary_content)
            
            return {
                "status": "success",
                "format": "stl_binary",
                "file_path": str(output_file),
                "file_size_mb": output_file.stat().st_size / (1024 * 1024),
                "triangle_count": len(vertices)
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _convert_to_obj(self, stl_file: Path, output_file: Path, quality: str) -> Dict:
        """Convert STL to OBJ format"""
        try:
            vertices = self._parse_binary_stl_vertices(stl_file)
            obj_content = self._generate_obj(vertices, quality)
            
            output_file.write_text(obj_content)
            
            return {
                "status": "success",
                "format": "obj",
                "quality": quality,
                "file_path": str(output_file),
                "file_size_mb": output_file.stat().st_size / (1024 * 1024),
                "vertex_count": len(vertices)
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _convert_to_step(self, job_id: str, output_file: Path) -> Dict:
        """Convert to STEP format (requires Rhino Compute)"""
        return {
            "status": "requires_rhino",
            "format": "step",
            "message": "STEP export requires Rhino Compute integration",
            "instructions": [
                "1. Ensure Rhino Compute is running",
                "2. POST /cad/export/{job_id}/step",
                "3. Processing will use Rhino's native conversion"
            ]
        }
    
    async def _convert_to_iges(self, job_id: str, output_file: Path) -> Dict:
        """Convert to IGES format (requires Rhino Compute)"""
        return {
            "status": "requires_rhino",
            "format": "iges",
            "message": "IGES export requires Rhino Compute integration",
            "instructions": [
                "1. Ensure Rhino Compute is running",
                "2. POST /cad/export/{job_id}/iges",
                "3. Processing will use Rhino's native conversion"
            ]
        }
    
    def _parse_binary_stl_vertices(self, file_path: Path) -> list:
        """Parse vertices from binary STL"""
        vertices = []
        
        with open(file_path, 'rb') as f:
            # Skip header
            f.read(80)
            
            # Read triangle count
            tri_count_bytes = f.read(4)
            tri_count = struct.unpack('<I', tri_count_bytes)[0]
            
            # Read vertices
            for _ in range(tri_count):
                # Skip normal vector (3 floats)
                f.read(12)
                
                # Read 3 vertices (9 floats)
                for _ in range(3):
                    v = struct.unpack('<fff', f.read(12))
                    vertices.append(v)
                
                # Skip attribute byte count
                f.read(2)
        
        return vertices
    
    def _parse_ascii_stl_vertices(self, file_path: Path) -> list:
        """Parse vertices from ASCII STL"""
        vertices = []
        content = file_path.read_text()
        
        # Find all vertex lines
        pattern = r'vertex\s+([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)\s+([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)\s+([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)'
        
        for match in re.finditer(pattern, content):
            x = float(match.group(1))
            y = float(match.group(3))
            z = float(match.group(5))
            vertices.append((x, y, z))
        
        return vertices
    
    def _generate_ascii_stl(self, vertices: list) -> str:
        """Generate ASCII STL from vertices"""
        lines = ["solid model"]
        
        # Process vertices in groups of 3 (triangles)
        for i in range(0, len(vertices), 3):
            if i + 2 < len(vertices):
                v1, v2, v3 = vertices[i], vertices[i+1], vertices[i+2]
                
                # Calculate normal (simple cross product)
                nx = (v2[1]-v1[1])*(v3[2]-v1[2]) - (v2[2]-v1[2])*(v3[1]-v1[1])
                ny = (v2[2]-v1[2])*(v3[0]-v1[0]) - (v2[0]-v1[0])*(v3[2]-v1[2])
                nz = (v2[0]-v1[0])*(v3[1]-v1[1]) - (v2[1]-v1[1])*(v3[0]-v1[0])
                
                # Normalize
                length = (nx**2 + ny**2 + nz**2) ** 0.5
                if length > 0:
                    nx, ny, nz = nx/length, ny/length, nz/length
                
                lines.append(f"  facet normal {nx:e} {ny:e} {nz:e}")
                lines.append("    outer loop")
                lines.append(f"      vertex {v1[0]:e} {v1[1]:e} {v1[2]:e}")
                lines.append(f"      vertex {v2[0]:e} {v2[1]:e} {v2[2]:e}")
                lines.append(f"      vertex {v3[0]:e} {v3[1]:e} {v3[2]:e}")
                lines.append("    endloop")
                lines.append("  endfacet")
        
        lines.append("endsolid model")
        return "\n".join(lines)
    
    def _generate_binary_stl(self, vertices: list) -> bytes:
        """Generate binary STL from vertices"""
        data = bytearray()
        
        # Write header (80 bytes)
        header = b"Binary STL from CAD Generation Pipeline".ljust(80, b'\0')
        data.extend(header)
        
        # Write triangle count
        triangle_count = len(vertices) // 3
        data.extend(struct.pack('<I', triangle_count))
        
        # Write triangles
        for i in range(0, len(vertices), 3):
            if i + 2 < len(vertices):
                v1, v2, v3 = vertices[i], vertices[i+1], vertices[i+2]
                
                # Calculate normal
                nx = (v2[1]-v1[1])*(v3[2]-v1[2]) - (v2[2]-v1[2])*(v3[1]-v1[1])
                ny = (v2[2]-v1[2])*(v3[0]-v1[0]) - (v2[0]-v1[0])*(v3[2]-v1[2])
                nz = (v2[0]-v1[0])*(v3[1]-v1[1]) - (v2[1]-v1[1])*(v3[0]-v1[0])
                
                # Normalize
                length = (nx**2 + ny**2 + nz**2) ** 0.5
                if length > 0:
                    nx, ny, nz = nx/length, ny/length, nz/length
                
                # Write normal
                data.extend(struct.pack('<fff', nx, ny, nz))
                
                # Write vertices
                data.extend(struct.pack('<fff', *v1))
                data.extend(struct.pack('<fff', *v2))
                data.extend(struct.pack('<fff', *v3))
                
                # Write attribute byte count
                data.extend(struct.pack('<H', 0))
        
        return bytes(data)
    
    def _generate_obj(self, vertices: list, quality: str) -> str:
        """Generate OBJ from vertices"""
        lines = [
            "# OBJ file generated from CAD model",
            "# Generated by CAD Pipeline",
            ""
        ]
        
        # Write vertices
        for i, v in enumerate(vertices):
            lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
        
        # Write faces
        for i in range(0, len(vertices), 3):
            if i + 2 < len(vertices):
                v1_idx = i + 1
                v2_idx = i + 2
                v3_idx = i + 3
                lines.append(f"f {v1_idx} {v2_idx} {v3_idx}")
        
        # Add material hint
        lines.extend([
            "",
            "# Material properties",
            "usemtl plastic",
            "# End of OBJ file"
        ])
        
        return "\n".join(lines)


def get_export_manager() -> ExportManager:
    """Get export manager instance"""
    return ExportManager()
