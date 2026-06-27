"""
cone_template.py - Grasshopper GhPython Template

Copy this code into a GhPython component in Grasshopper.

Inputs (numbered sliders):
  - R (Radius): 1-2500 mm
  - H (Height): 1-5000 mm
  - TR (TipRadius): 0-500 mm

Output:
  - BaseGeometry: Brep object
"""

import Rhino.Geometry as rg

def create_cone(radius, height, tip_radius):
    """Create a cone or truncated cone (frustum)"""
    
    plane = rg.Plane(rg.Point3d(0, 0, 0), rg.Vector3d(0, 0, 1))
    
    if tip_radius > 0:
        # Create frustum using loft
        base_circle = rg.Circle(plane, radius)
        top_plane = rg.Plane(rg.Point3d(0, 0, height), rg.Vector3d(0, 0, 1))
        top_circle = rg.Circle(top_plane, tip_radius)
        
        loft_curves = [base_circle.ToNurbsCurve(), top_circle.ToNurbsCurve()]
        breps = rg.Brep.CreateFromLoft(
            loft_curves,
            rg.Point3d.Unset,
            rg.Point3d.Unset,
            rg.LoftType.Normal,
            False
        )
        
        brep = breps[0] if breps and len(breps) > 0 else None
    else:
        # Create true cone
        cone = rg.Cone(plane, height, radius)
        brep = cone.ToBrep()
    
    return brep

# Input validation
R = max(0.1, float(R)) if R else 50
H = max(0.1, float(H)) if H else 100
TR = max(0, float(TR)) if TR else 0

# Generate geometry
BaseGeometry = create_cone(R, H, TR)
