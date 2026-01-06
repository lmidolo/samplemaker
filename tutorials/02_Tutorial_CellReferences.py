"""
02_Tutorial_CellReferences
"""


# In this tutorial we learn to create multiple GDS cells and instantiate 
# references (single or array)

# Let's import basic stuff
import samplemaker.layout as smlay # used for layout 
import samplemaker.makers as sm # used for drawing

# Create a simple mask layout
themask = smlay.Mask("02_Tutorial_CellReferences")

# Let's draw a simple shape
base = sm.make_rect(0,0,2,10)
base += sm.make_circle(4,5,1,to_poly=True)

# We would like to make identical copies of this.
# Instead of using base.copy() which duplicates the memory and GDS file size
# we can place base in a GDS CELL and refer to it in our main cell

# Create a new GDS cell called "BCELL"
themask.addCell("BCELL", base)

# Now create a single reference to it 
geomE = sm.make_sref(20, 15, "BCELL", base,mag=1.0,angle=0,mirror=False)
# Note that we can move, rotate, scale and mirror the reference 

# Let's create another instance but scaledby 50%  and rotated by 45 degrees
geomE += sm.make_sref(40, 15, "BCELL", base,mag=1.5,angle=45,mirror=False)

# Now geomE contains a single instance of BCELL

# We can continue and make another base cell with a different name
b2 = sm.make_rounded_rect(0, 0, 7, 3, 1)
# We can add an instance of BCELL, the only rule is avoiding cyclic references
b2 +=sm.make_sref(10, 0, "BCELL", base)

# Now let's add this to the layout and call it B_TWO
themask.addCell("B_TWO", b2)

# Referring to B_TWO in the main cell will include both B_TWO and a reference to BASE
# There is no limit in concatenating references. 
# Instead of creating a single reference, let's use reference arrays
# We can create an array of references on a regular grid specified by the unit cell vectors
geomE += sm.make_aref(0,50,"B_TWO",b2,3, 4, 25.0, 0.0, 0.0, 20.0)
# Above we created a reference starting in (0,50) and a grid with 3 rows and 4 columns
# the unit cell vectors are [25,0] and [0,20], i.e. a rectangular grid.

# If you at any point require flattening the geometry, you simply call
geomFlatten = geomE.flatten()
# Note that flatten() creates a new geometry that needs to be stored.
# You can pass a list of layer to flatten to only select some of the layers during the flattening process
# You need flattening to perform boolean operations with SREF/AREF, otherwise those entities will be ignored.
themask.addCell("FLATCELL",geomFlatten)

# Instantiate it into the main cell
geomE += sm.make_sref(150, 0, "FLATCELL", geomFlatten)

# Let's add all to main cell
themask.addToMainCell(geomE)    

# Export to GDS
themask.exportGDS()

# Finished!