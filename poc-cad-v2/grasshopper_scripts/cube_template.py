"""
cube_template.py - Grasshopper GhPython Template

Copy this code into a GhPython component in Grasshopper.

Inputs (numbered sliders):
  - L (Length): 0-5000 mm
  - W (Width): 0-5000 mm
  - H (Height): 0-5000 mm
  - FR (FilletRadius): 0-500 mm

Output:
  - BaseGeometry: Brep object
"""

import Rhino.Geometry as rg

def create_cube(length, width, height, fillet_radius):
    """Create a cube or rounded cube"""
    
    # Create base box
    plane = rg.Plane.WorldXY
    box = rg.Box(plane, length, width, height)
    brep = rg.Brep.CreateFromBox(box)
    
    # Apply fillet if radius > 0
    if fillet_radius > 0:
        try:
            edges = brep.Edges
            edge_indices = [i for i in range(edges.Count)]
            tolerance = 0.01
            
            # Create fillet
            fillet_breps = rg.Brep.CreateFilletedBreps(
                brep, 
                edge_indices, 
                fillet_radius, 
                tolerance
            )
            
            if fillet_breps and len(fillet_breps) > 0:
                brep = fillet_breps[0]
        except:
            pass  # Silently fail, return non-filleted cube
    
    return brep

# Input validation
L = max(0.1, float(L)) if L else 100
W = max(0.1, float(W)) if W else 100
H = max(0.1, float(H)) if H else 100
FR = max(0, float(FR)) if FR else 0

# Generate geometry
BaseGeometry = create_cube(L, W, H, FR)
