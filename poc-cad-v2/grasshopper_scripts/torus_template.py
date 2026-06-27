"""
torus_template.py - Grasshopper GhPython Template

Copy this code into a GhPython component in Grasshopper.

Inputs (numbered sliders):
  - MR (MajorRadius): 10-2500 mm
  - mr (MinorRadius): 1-1000 mm

Output:
  - BaseGeometry: Brep object
"""

import Rhino.Geometry as rg
import math

def create_torus(major_radius, minor_radius):
    """Create a torus using lofted circles"""
    
    # Create profile circles around major circle
    circle_count = 24
    major_circle = rg.Circle(rg.Plane.WorldXY, major_radius)
    profiles = []
    
    for i in range(circle_count):
        angle = (2 * math.pi * i) / circle_count
        circle_center = major_circle.PointAt(angle)
        plane = rg.Plane(circle_center, rg.Vector3d.ZAxis)
        profile = rg.Circle(plane, minor_radius)
        profiles.append(profile.ToNurbsCurve())
    
    # Close the loop
    profiles.append(profiles[0])
    
    # Create lofted surface
    breps = rg.Brep.CreateFromLoft(
        profiles,
        rg.Point3d.Unset,
        rg.Point3d.Unset,
        rg.LoftType.Normal,
        True  # Closed
    )
    
    brep = breps[0] if breps and len(breps) > 0 else None
    return brep

# Input validation
MR = max(1, float(MR)) if MR else 100
mr = max(0.1, float(mr)) if mr else 20

# Generate geometry
BaseGeometry = create_torus(MR, mr)
