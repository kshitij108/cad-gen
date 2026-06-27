"""
STL File Validation and Quality Assurance
Validates generated STL files for manufacturability
"""

import os
import struct
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class STLValidationResult:
    """Results of STL validation"""
    is_valid: bool
    file_size_mb: float
    triangle_count: int
    has_issues: bool
    issues: List[str]
    warnings: List[str]
    bounds: Optional[Dict[str, float]] = None
    volume: Optional[float] = None


class STLValidator:
    """Validates STL files for manufacturability and quality"""
    
    # Maximum recommended file size (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024
    
    # Maximum triangle count (5 million)
    MAX_TRIANGLES = 5_000_000
    
    # Minimum triangle count (at least a basic shape)
    MIN_TRIANGLES = 4
    
    # Maximum dimension difference (for detecting malformed geometry)
    MAX_DIMENSION = 10000  # 10 meters
    MIN_DIMENSION = 0.1  # 0.1mm
    
    def __init__(self):
        pass
    
    def validate_file(self, file_path: str) -> STLValidationResult:
        """
        Validate an STL file
        
        Args:
            file_path: Path to STL file
            
        Returns:
            STLValidationResult with validation details
        """
        file_path = Path(file_path)
        issues = []
        warnings = []
        
        # Check file exists
        if not file_path.exists():
            return STLValidationResult(
                is_valid=False,
                file_size_mb=0,
                triangle_count=0,
                has_issues=True,
                issues=["File does not exist"],
                warnings=[]
            )
        
        # Check file size
        file_size = file_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        if file_size > self.MAX_FILE_SIZE:
            issues.append(f"File size {file_size_mb:.2f}MB exceeds limit of {self.MAX_FILE_SIZE / (1024*1024):.2f}MB")
        
        if file_size < 80:  # Minimum valid STL size (header + 1 triangle)
            issues.append("File is too small to be a valid STL")
            return STLValidationResult(
                is_valid=False,
                file_size_mb=file_size_mb,
                triangle_count=0,
                has_issues=True,
                issues=issues,
                warnings=warnings
            )
        
        # Detect ASCII vs Binary format
        is_ascii = self._is_ascii_stl(file_path)
        
        # Parse STL
        try:
            if is_ascii:
                triangle_count, bounds = self._parse_ascii_stl(file_path)
            else:
                triangle_count, bounds = self._parse_binary_stl(file_path)
        except Exception as e:
            issues.append(f"Failed to parse STL: {str(e)}")
            return STLValidationResult(
                is_valid=False,
                file_size_mb=file_size_mb,
                triangle_count=0,
                has_issues=True,
                issues=issues,
                warnings=warnings
            )
        
        # Validate triangle count
        if triangle_count < self.MIN_TRIANGLES:
            issues.append(f"Too few triangles ({triangle_count}), minimum is {self.MIN_TRIANGLES}")
        
        if triangle_count > self.MAX_TRIANGLES:
            warnings.append(f"High triangle count ({triangle_count}) may cause performance issues")
        
        # Validate bounds
        if bounds:
            for axis in ['x', 'y', 'z']:
                min_val = bounds[f'{axis}_min']
                max_val = bounds[f'{axis}_max']
                dimension = max_val - min_val
                
                if dimension > self.MAX_DIMENSION:
                    issues.append(f"Dimension on {axis.upper()} axis ({dimension:.2f}) exceeds max ({self.MAX_DIMENSION})")
                
                if 0 < dimension < self.MIN_DIMENSION:
                    warnings.append(f"Very small dimension on {axis.upper()} axis ({dimension:.6f}mm)")
        
        # Validate no NaN or Inf values
        if bounds:
            for key, value in bounds.items():
                if value is None or (isinstance(value, float) and (value != value or value == float('inf'))):
                    issues.append(f"Invalid value detected in bounds: {key}")
        
        is_valid = len(issues) == 0
        has_issues = len(issues) > 0
        
        return STLValidationResult(
            is_valid=is_valid,
            file_size_mb=file_size_mb,
            triangle_count=triangle_count,
            has_issues=has_issues,
            issues=issues,
            warnings=warnings,
            bounds=bounds
        )
    
    def _is_ascii_stl(self, file_path: Path) -> bool:
        """Check if STL is ASCII or binary format"""
        try:
            with open(file_path, 'rb') as f:
                # Read first 5 bytes
                header = f.read(5)
                # ASCII STL starts with "solid"
                return header.startswith(b'solid')
        except:
            return False
    
    def _parse_ascii_stl(self, file_path: Path) -> Tuple[int, Dict]:
        """Parse ASCII STL and extract metadata"""
        triangle_count = 0
        bounds = {'x_min': float('inf'), 'x_max': float('-inf'),
                  'y_min': float('inf'), 'y_max': float('-inf'),
                  'z_min': float('inf'), 'z_max': float('-inf')}
        
        try:
            with open(file_path, 'r', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('facet normal'):
                        triangle_count += 1
                    elif line.startswith('vertex'):
                        coords = line.split()
                        if len(coords) == 4:
                            x, y, z = float(coords[1]), float(coords[2]), float(coords[3])
                            bounds['x_min'] = min(bounds['x_min'], x)
                            bounds['x_max'] = max(bounds['x_max'], x)
                            bounds['y_min'] = min(bounds['y_min'], y)
                            bounds['y_max'] = max(bounds['y_max'], y)
                            bounds['z_min'] = min(bounds['z_min'], z)
                            bounds['z_max'] = max(bounds['z_max'], z)
        except Exception as e:
            raise ValueError(f"Error parsing ASCII STL: {e}")
        
        # Clean up infinity values
        for key in bounds:
            if bounds[key] == float('inf') or bounds[key] == float('-inf'):
                bounds[key] = None
        
        return triangle_count, bounds
    
    def _parse_binary_stl(self, file_path: Path) -> Tuple[int, Dict]:
        """Parse binary STL and extract metadata"""
        bounds = {'x_min': float('inf'), 'x_max': float('-inf'),
                  'y_min': float('inf'), 'y_max': float('-inf'),
                  'z_min': float('inf'), 'z_max': float('-inf')}
        
        try:
            with open(file_path, 'rb') as f:
                # Skip 80-byte header
                f.read(80)
                
                # Read triangle count (4-byte unsigned int, little-endian)
                triangle_count_bytes = f.read(4)
                triangle_count = struct.unpack('<I', triangle_count_bytes)[0]
                
                # Parse each triangle (50 bytes each)
                for _ in range(triangle_count):
                    # Skip normal vector (3 floats = 12 bytes)
                    f.read(12)
                    
                    # Read 3 vertices (3 floats each = 36 bytes)
                    for _ in range(3):
                        x_bytes = f.read(4)
                        y_bytes = f.read(4)
                        z_bytes = f.read(4)
                        
                        if len(x_bytes) == 4 and len(y_bytes) == 4 and len(z_bytes) == 4:
                            x = struct.unpack('<f', x_bytes)[0]
                            y = struct.unpack('<f', y_bytes)[0]
                            z = struct.unpack('<f', z_bytes)[0]
                            
                            bounds['x_min'] = min(bounds['x_min'], x)
                            bounds['x_max'] = max(bounds['x_max'], x)
                            bounds['y_min'] = min(bounds['y_min'], y)
                            bounds['y_max'] = max(bounds['y_max'], y)
                            bounds['z_min'] = min(bounds['z_min'], z)
                            bounds['z_max'] = max(bounds['z_max'], z)
                    
                    # Skip attribute byte count (2 bytes)
                    f.read(2)
        except Exception as e:
            raise ValueError(f"Error parsing binary STL: {e}")
        
        # Clean up infinity values
        for key in bounds:
            if bounds[key] == float('inf') or bounds[key] == float('-inf'):
                bounds[key] = None
        
        return triangle_count, bounds
    
    def get_quality_score(self, validation_result: STLValidationResult) -> float:
        """
        Calculate quality score (0-100) based on validation results
        
        Args:
            validation_result: STLValidationResult object
            
        Returns:
            Quality score from 0 to 100
        """
        score = 100.0
        
        # Deduct points for issues
        score -= len(validation_result.issues) * 20
        
        # Deduct points for warnings
        score -= len(validation_result.warnings) * 5
        
        # Deduct points for extreme file sizes
        if validation_result.file_size_mb > 50:
            score -= 10
        
        # Deduct points for extreme triangle counts
        if validation_result.triangle_count > 1_000_000:
            score -= 5
        
        return max(0, min(100, score))


def validate_stl_file(file_path: str) -> Dict:
    """
    Convenience function to validate an STL file
    
    Args:
        file_path: Path to STL file
        
    Returns:
        Dictionary with validation results
    """
    validator = STLValidator()
    result = validator.validate_file(file_path)
    
    return {
        "is_valid": result.is_valid,
        "file_size_mb": result.file_size_mb,
        "triangle_count": result.triangle_count,
        "has_issues": result.has_issues,
        "issues": result.issues,
        "warnings": result.warnings,
        "bounds": result.bounds,
        "quality_score": validator.get_quality_score(result)
    }
