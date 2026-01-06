"""
04_Tutorial_Boolean
"""


# In this tutorial we learn how to do boolean operations between groups of 
# polygons

# Let's import basic stuff
import samplemaker.layout as smlay # used for layout 
import samplemaker.makers as sm # used for drawing

# Create a simple mask layout
themask = smlay.Mask("04_Tutorial_Boolean")

# Empty geometry
geomE = sm.GeomGroup()

# Let's make a large box
box0 = sm.make_rect(0,0,100,100,layer=1)

# And some text, because text is complex polygons!
text0 = sm.make_text(0, 0, "DIFF", 10, 2,angle=30,to_poly=True,layer=1)

# Let's take the boolean difference box-text
bdiff = box0.copy() # Note that boolean operations alter the original element so we need to make a copy first
bdiff.boolean_difference(text0, 1, 1)
# The first integer is the layer from which you should subtract and the second is the subtracted layer
# Now bdiff is box-text
geomE+=bdiff

# Now let's try intersection (AND operation)
# Let's use two overlapping texts, slighlty larger
text1 = sm.make_text(0,0,"DIFF",11,3,angle=30,to_poly=True,layer=1)
text1.boolean_intersection(text0, 1, 1)
text1.translate(100, 0)
geomE+=text1

# XOR is also quite useful, only keeps parts that are not in both
text2 = sm.make_text(50,0,"XOR",10,1,angle=0,to_poly=True,layer=1)
text2.boolean_xor(box0, 1, 1)
text2.translate(200, 0)
geomE+=text2

# Trapezoid slicing, useful for some e-beam export
trapz = text2.copy()
trapz.trapezoids(1)
trapz.translate(150, 0)
geomE+=trapz

# Union, we could re-unite all trapezoids in the previous
uni1 = trapz.copy()
uni1.boolean_union(1)
uni1.translate(150, 0)
geomE+=uni1

# Just for fun, outlining the last result
out1 = uni1.copy()
out1.poly_outlining(1, 1)
out1.translate(150, 0)
geomE+=out1

# Let's add all to main cell
themask.addToMainCell(geomE)    

# Export to GDS
themask.exportGDS()

# Finished!