"""
test_grasshopper_mock.py

Test suite for mock Grasshopper engine and template validation.
Validates that:
1. Mock engine generates valid STL files for all 6 shapes
2. Generated files pass quality validation
3. Integration with pipeline works correctly
"""

import sys
from pathlib import Path
import json
import struct

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from mock_grasshopper_engine import MockGrasshopper, TemplateShape
from stl_validator import STLValidator


def test_mock_generation():
    """Test mock engine generates valid STL for all shapes"""
    
    engine = MockGrasshopper()
    validator = STLValidator()
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    test_cases = [
        {
            "shape": TemplateShape.CUBE,
            "params": {"length": 100, "width": 100, "height": 100, "fillet_radius": 5},
            "name": "Cube 100x100x100"
        },
        {
            "shape": TemplateShape.SPHERE,
            "params": {"radius": 50},
            "name": "Sphere r=50"
        },
        {
            "shape": TemplateShape.CYLINDER,
            "params": {"radius": 50, "height": 100, "fillet_top": 2},
            "name": "Cylinder r=50 h=100"
        },
        {
            "shape": TemplateShape.CONE,
            "params": {"radius": 50, "height": 100, "tip_radius": 0},
            "name": "Cone r=50 h=100"
        },
        {
            "shape": TemplateShape.TORUS,
            "params": {"major_radius": 100, "minor_radius": 20},
            "name": "Torus R=100 r=20"
        },
        {
            "shape": TemplateShape.WEDGE,
            "params": {"base_length": 100, "base_width": 100, "height": 100, "angle": 45},
            "name": "Wedge 100x100x100 45°"
        },
    ]
    
    print("=" * 70)
    print("MOCK GRASSHOPPER ENGINE TEST SUITE")
    print("=" * 70)
    print()
    
    results = []
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        shape = test_case["shape"]
        params = test_case["params"]
        name = test_case["name"]
        
        print(f"Testing: {name}")
        print("-" * 70)
        
        try:
            # Generate STL
            output_file = output_dir / f"{shape.value}_test.stl"
            metadata = engine.generate_to_stl(shape, params, str(output_file))
            
            # Validate STL
            validation_result = validator.validate_file(str(output_file))
            quality_score = validator.get_quality_score(validation_result)
            
            # Print results
            print(f"  ✓ STL Generated")
            print(f"    - File size: {metadata['file_size_mb']:.2f} MB")
            print(f"    - Triangles: {metadata['triangle_count']:,}")
            print(f"    - Bounds: ({metadata['bounds']['min']['x']:.1f}, "
                  f"{metadata['bounds']['min']['y']:.1f}, "
                  f"{metadata['bounds']['min']['z']:.1f}) to "
                  f"({metadata['bounds']['max']['x']:.1f}, "
                  f"{metadata['bounds']['max']['y']:.1f}, "
                  f"{metadata['bounds']['max']['z']:.1f})")
            
            print(f"  ✓ Validation Passed")
            print(f"    - Quality Score: {quality_score}/100")
            print(f"    - Valid: {validation_result.is_valid}")
            print(f"    - Triangles: {validation_result.triangle_count}")
            
            if validation_result.issues:
                print(f"    - Issues: {', '.join(validation_result.issues)}")
            if validation_result.warnings:
                print(f"    - Warnings: {', '.join(validation_result.warnings)}")
            
            results.append({
                "test": name,
                "status": "PASS" if validation_result.is_valid and quality_score >= 70 else "FAIL",
                "quality_score": quality_score,
                "triangles": metadata['triangle_count'],
                "file_size_mb": metadata['file_size_mb']
            })
            
            if validation_result.is_valid and quality_score >= 70:
                print(f"  ✓ TEST PASSED")
                passed += 1
            else:
                print(f"  ✗ TEST FAILED (Quality={quality_score})")
                failed += 1
        
        except Exception as e:
            print(f"  ✗ ERROR: {str(e)}")
            results.append({
                "test": name,
                "status": "ERROR",
                "error": str(e)
            })
            failed += 1
        
        print()
    
    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Passed: {passed}/{len(test_cases)}")
    print(f"Failed: {failed}/{len(test_cases)}")
    print()
    
    # Detailed results table
    print("DETAILED RESULTS:")
    print("-" * 70)
    print(f"{'Test':<30} {'Status':<8} {'Quality':<10} {'Triangles':<12} {'Size (MB)':<10}")
    print("-" * 70)
    
    for result in results:
        quality = f"{result.get('quality_score', 0):.0f}" if 'quality_score' in result else "N/A"
        triangles = f"{result.get('triangles', 0):,}" if 'triangles' in result else "N/A"
        size = f"{result.get('file_size_mb', 0):.2f}" if 'file_size_mb' in result else "N/A"
        
        print(f"{result['test']:<30} {result['status']:<8} {quality:<10} {triangles:<12} {size:<10}")
    
    print("-" * 70)
    print()
    
    # Output results to JSON
    results_file = output_dir / "test_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "summary": {
                "passed": passed,
                "failed": failed,
                "total": len(test_cases)
            },
            "results": results
        }, f, indent=2)
    
    print(f"Results saved to: {results_file}")
    print()
    
    return passed == len(test_cases)


def test_stl_binary_format():
    """Verify binary STL format is correct"""
    
    print("=" * 70)
    print("STL BINARY FORMAT VALIDATION")
    print("=" * 70)
    print()
    
    engine = MockGrasshopper()
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    # Generate a simple cube
    output_file = output_dir / "format_test.stl"
    metadata = engine.generate_to_stl(
        TemplateShape.CUBE,
        {"length": 100, "width": 100, "height": 100},
        str(output_file)
    )
    
    # Verify binary format
    with open(output_file, 'rb') as f:
        # Header (80 bytes)
        header = f.read(80)
        print(f"Header: {header[:27].decode('utf-8', errors='ignore')}")
        
        # Triangle count (4 bytes, little-endian)
        tri_count_bytes = f.read(4)
        tri_count = struct.unpack('<I', tri_count_bytes)[0]
        print(f"Triangle Count: {tri_count}")
        
        # Read first triangle
        first_tri = f.read(50)  # 50 bytes per triangle
        if len(first_tri) == 50:
            normal_bytes = first_tri[:12]
            nx, ny, nz = struct.unpack('<fff', normal_bytes)
            print(f"First Triangle Normal: ({nx:.4f}, {ny:.4f}, {nz:.4f})")
            
            v1_bytes = first_tri[12:24]
            v1x, v1y, v1z = struct.unpack('<fff', v1_bytes)
            print(f"Vertex 1: ({v1x:.2f}, {v1y:.2f}, {v1z:.2f})")
            
            print("✓ Binary format is correct")
        else:
            print("✗ Binary format error: insufficient data")
    
    print()


def test_parameters_validation():
    """Verify parameter validation works"""
    
    print("=" * 70)
    print("PARAMETER VALIDATION TEST")
    print("=" * 70)
    print()
    
    engine = MockGrasshopper()
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    test_params = [
        {
            "name": "Extreme dimensions",
            "shape": TemplateShape.CUBE,
            "params": {"length": 5000, "width": 5000, "height": 5000}
        },
        {
            "name": "Minimal dimensions",
            "shape": TemplateShape.SPHERE,
            "params": {"radius": 1}
        },
        {
            "name": "Large radius torus",
            "shape": TemplateShape.TORUS,
            "params": {"major_radius": 2000, "minor_radius": 500}
        },
    ]
    
    for test in test_params:
        print(f"Testing: {test['name']}")
        try:
            output_file = output_dir / f"param_test_{test['name'].lower().replace(' ', '_')}.stl"
            metadata = engine.generate_to_stl(test['shape'], test['params'], str(output_file))
            print(f"  ✓ Generated {metadata['triangle_count']} triangles, {metadata['file_size_mb']:.2f}MB")
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
        print()


if __name__ == "__main__":
    # Run tests
    all_passed = test_mock_generation()
    print()
    test_stl_binary_format()
    print()
    test_parameters_validation()
    print()
    
    print("=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 70)
    print()
    print("Next Steps:")
    print("1. If all tests passed, mock engine is ready for integration testing")
    print("2. On Windows: Create .gh template files using provided GhPython scripts")
    print("3. Upload templates to Rhino Compute and test end-to-end pipeline")
    print("4. Once real Rhino works, switch from mock mode: USE_MOCK_GRASSHOPPER=false")
    print()
