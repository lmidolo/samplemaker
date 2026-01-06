"""
00_Tutorial_BasicDrawing
"""

import samplemaker.layout as smlay # used for layout 
import samplemaker.makers as sm # used for drawing
from samplemaker.viewers import GeomView # Used to inspect drawing before viewing

# Create a simple mask layout
themask = smlay.Mask("00_Tutorial_BasicDrawing")

# THe idea of basic drawing is to place geometry elements and manipulate them
# When we are happy we add them to the mask and write to GDS.

# IMPORTANT: all units are in um

# The samplemaker.makers contains all make_ functions required to draw.
# These functions return a geometry group that can be combined with other geometries

# Example: draw a rectangle centered in (2.0,3.0) width of 8 um and height of 2 um
re0 = sm.make_rect(x0=2,y0=3,width=8,height=2)

# Rotate the rectangle by 30 degrees around its center
re0.rotate(2, 3, 30)

# Create a copy of the rectangle
re1 = re0.copy()

# Change the layer of the copy
re1.set_layer(3)

# Shift the copy by 20 um to the right
re1.translate(20, 0)

# Ok now combine the two rectangle in the same geometry
re0+=re1 # re0 contains both, you can still change re1!

# To reduce the amount of lines of code you can combine a sequence of operations
# Note that this will first copy, then translate, then scale, setting the layer and finally adding to re0
# It is very common to copy and then translate or change layer. The following allows it to do this explicitly
re0 += re1.copy().translate(20,0).scale(40,0,1.2,2.2).set_layer(6)

# mirror both in the Y direction around the x=0 axis 
re0.mirrorY(0)

# We can inspect the geometry using GeomView
GeomView(re0)

# To add the rectangles to the final layout use addToMainCell()
themask.addToMainCell(re0)

# Export to GDS
themask.exportGDS()

# Finished!