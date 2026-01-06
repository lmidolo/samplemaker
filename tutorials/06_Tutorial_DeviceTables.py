"""
06_Tutorial_DeviceTables
"""


# Here we look at how to organize devices in different files, for reusing them over different scripts.
# We moved the device from the previous tutorial into a separate file
# and we called it TutorialCollection.py. Check out this file before starting.

# Let's import basic stuff
import samplemaker.layout as smlay # used for layout 
import samplemaker.makers as sm # used for drawing
import samplemaker.devices as smdev # used for device function
import TutorialCollection # Let's import the tutorial collection of devices, they get automagically registered
# Let's use numpy arrays
import numpy as np

# Create a simple mask layout
themask = smlay.Mask("06_Tutorial_DeviceTables")

# Empty geometry
geomE = sm.GeomGroup()

# Let's first build a device that we would like to place in a table
# we will use the Free-free membrane of the previous tutorial
dev = smdev.Device.build_registered("CUSTOM_FFM")

# To create a table, we can use the DeviceTable() function in the layout package
tab = smlay.DeviceTable(dev, 3, 5, {"R":np.array([35,40,46])}, {"L":np.array([40,40,44,44,50])})
# This will create a 3x5 matrix (3 rows and 5 columns) 
# Along rows, we are changing the R parameter of the free-free membrane, while along columns we are changing the length

# By default, the table is aligned so that each cell is centered and the 
# distance between element is zero. To change it and increase the distance to, say, 10 um in x and y:
tab.auto_align(10, 10, numkey=1)
# the numkey can be used to specify which position should be used for alignment (1 means lower left corner of each table cell).,


# We can add some annotations (i.e. text) around the table (a bit like table headers)
tab.set_annotations(smlay.DeviceTableAnnotations("R=%R0", "L=%C0", 
                                                          80, 80, 
                                                          ("R",),("L",)))

# In the above function, the first two arguments are the text format for columns and rows, respectively.
# The format can contain any string text and special symbols like %C0, %C1... or %R0, %R1.. that will be 
# replaced with the actual column and row value. The index refers to the list of column and row variables
# provided as a tuple ("L",). You can pick any variable. 
# you can also use %I or %J to get the column and row number as integers
# The values 80, 80 indicate how much offset there should be to the edge of the table for cols and rows.
# Optionally, you can specify text_width and text_height.
# By default headers are created on all four sides, to switch off one side, specify left=False or right=False
# below=False, above=False.

# Finally, we add the device table to the mask and place it so that its center is at position 150,150.
themask.addDeviceTable(tab, 150, 150)

# Export to GDS
themask.exportGDS()

# Finished!