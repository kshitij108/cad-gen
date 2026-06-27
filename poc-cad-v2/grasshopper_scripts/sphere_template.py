"""
sphere_template.py - Grasshopper GhPython Template

Copy this code into a GhPython component in Grasshopper.

Inputs (numbered sliders):
  - R (Radius): 1-2500 mm

Output:
  - BaseGeometry: Brep object
"""

import Rhino.Geometry as rg

def create_sphere(radius):
    """Create a sphere"""
    
    sphere = rg.Sphere(rg.Point3d.Origin, radius)
    brep = sphere.ToBrep()
    
    return brep

# Input validation
R = max(0.1, float(R)) if R else 50

# Generate geometry
BaseGeometry = create_sphere(R)
