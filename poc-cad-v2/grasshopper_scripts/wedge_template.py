"""
wedge_template.py - Grasshopper GhPython Template

Copy this code into a GhPython component in Grasshopper.

Inputs (numbered sliders):
  - BL (BaseLength): 1-5000 mm
  - BW (BaseWidth): 1-5000 mm
  - H (Height): 1-5000 mm
  - A (Angle): 1-89 degrees

Output:
  - BaseGeometry: Brep object
"""

import Rhino.Geometry as rg
import math

def create_wedge(base_length, base_width, height, angle_deg):
    """Create a wedge (angled prism)"""
    
    angle_rad = math.radians(angle_deg)
    horizontal_offset = height / math.tan(angle_rad)
    
    # Define vertices
    p1 = rg.Point3d(0, 0, 0)
    p2 = rg.Point3d(base_length, 0, 0)
    p3 = rg.Point3d(base_length, base_width, 0)
    p4 = rg.Point3d(0, base_width, 0)
    
    p5 = rg.Point3d(horizontal_offset, 0, height)
    p6 = rg.Point3d(base_length + horizontal_offset, 0, height)
    p7 = rg.Point3d(base_length + horizontal_offset, base_width, height)
    p8 = rg.Point3d(horizontal_offset, base_width, height)
    
    # Create polyline surfaces for each face
    # This is a simplified approach - use Box and Transform for production
    
    # Create base box
    plane = rg.Plane.WorldXY
    box = rg.Box(plane, base_length, base_width, height)
    brep = rg.Brep.CreateFromBox(box)
    
    # Apply shear transform
    shear_vector = rg.Vector3d(horizontal_offset, 0, 0)
    shear_transform = rg.Transform.Shear(
        rg.Plane.WorldXY,
        rg.Vector3d.ZAxis,
        shear_vector,
        1.0
    )
    brep.Transform(shear_transform)
    
    return brep

# Input validation
BL = max(0.1, float(BL)) if BL else 100
BW = max(0.1, float(BW)) if BW else 100
H = max(0.1, float(H)) if H else 100
A = max(1, min(89, float(A))) if A else 45

# Generate geometry
BaseGeometry = create_wedge(BL, BW, H, A)
