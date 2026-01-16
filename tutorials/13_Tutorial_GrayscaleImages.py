# -*- coding: utf-8 -*-
"""
13_Tutorial_GrayscaleImages
"""

# Let's import basic stuff
import samplemaker.layout as smlay # used for layout
import numpy as np 
from samplemaker.shapes import GSImage

# Create a simple mask layout
themask = smlay.Mask("13_Tutorial_GrayscaleImages")

# Let's add a greyscale image:
gsi = GSImage(x0 = 15, y0 = 30, width = 2, height = 10, # the rectangle containing the image
              pix_w = 0.1, pix_h = 0.1) # the width and height of the pixel
# Images are stored as 8-bit unsigned integers
# Black is 0
# White is 255

# Add a grayscale ramp (vertical gradient) from y=2 to y=3 (um) and starting at pixel value 0 to 128
gsi.add_rampV(2, 3, 0, 128)
# And another one from 7 to 8 um ramping from gray128 to black
gsi.add_rampV(7, 8, 128, 0)

# Fill the space in between the two ramps with a box of color gray128 
gsi.add_box(0,2,3,7,128)

# You can use any image importer (e.g. openCV) to read an image and copy the data to 
# gsi.im 
# as long as the image size matches gsi.Nx,gsi.Ny pixels

# Export this to a group. Each pixel will be assigned to a different layer. 
# layer_0 will correspond to black
# levels (80) specifies how many layer levels should be used. Here, 80 means that layer 80 will be color 255 
geomE = gsi.to_group(layer_0 = 0, levels = 80, merge=True)
# if you wish to leave each pixel as a single rectangle set merge=False

# Create a dose-layer table that assigns dose = 1.0 to layer 0 and dose = 3.5 to layer 80
doses = np.linspace(1.0,3.5,80)
layers = [l for l in range(80)]

# Let's add all to main cell
themask.addToMainCell(geomE)    

# Export to GDS
themask.exportGDS()
# and the dosetable
themask.exportDoseTable(doses, layers)

# Finished!