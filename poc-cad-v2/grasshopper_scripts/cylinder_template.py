"""
cylinder_template.py - Grasshopper GhPython Template

Copy this code into a GhPython component in Grasshopper.

Inputs (numbered sliders):
  - R (Radius): 1-2500 mm
  - H (Height): 1-5000 mm
  - FT (FilletTop): 0-250 mm

Output:
  - BaseGeometry: Brep object
"""

import Rhino.Geometry as rg

def create_cylinder(radius, height, fillet_top):
    """Create a cylinder with optional top fillet"""
    
    # Create cylinder
    plane = rg.Plane(rg.Point3d(0, 0, 0), rg.Vector3d(0, 0, 1))
    cylinder = rg.Cylinder(plane, radius, height)
    brep = cylinder.ToBrep()
    
    # Apply fillet to top edge if radius > 0
    if fillet_top > 0:
        try:
            edges = brep.Edges
            if edges.Count > 0:
                # Top circular edge is usually the last edge
                edge_index = edges.Count - 1
                tolerance = 0.01
                
                fillet_breps = rg.Brep.CreateFilletedBreps(
                    brep,
                    [edge_index],
                    fillet_top,
                    tolerance
                )
                
                if fillet_breps and len(fillet_breps) > 0:
                    brep = fillet_breps[0]
        except:
            pass
    
    return brep

# Input validation
R = max(0.1, float(R)) if R else 50
H = max(0.1, float(H)) if H else 100
FT = max(0, float(FT)) if FT else 0

# Generate geometry
BaseGeometry = create_cylinder(R, H, FT)
