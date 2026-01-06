"""
07_Tutorial_Waveguides
"""


# We now look at some more advanced features, i.e. how to make waveguides.
# We illustrate the sequencer object using the base waveguide library in samplemaker

import samplemaker.layout as smlay # used for layout 
import samplemaker.makers as sm # used for drawing
from samplemaker.baselib.waveguides import BaseWaveguideSequencer # Used for the sequencer
import samplemaker.baselib.devices

# Create a simple mask layout
themask = smlay.Mask("07_Tutorial_Waveguides")

# Empty geometry
geomE = sm.GeomGroup()

# We can draw waveguides using a custom sequencer provided in the baselib module
# Sequencers are a general class provided in samplemaker to create waveguides
# however here we use a derived class that can actually draw waveguides according to a specific process.
# Anyone can write its own sequencer instructions for its system.
# It is recommended to look at the baselib/ subfolder in the samplemaker source code
# to learn how to define your own drawing commands, specialized for your process.

# Step 1: the sequence
# Provide a list of commands + parameters to be executed by the sequencer
# For example, 
# S 10 : go straight (S) by 10 um
# B 90 3: bend by 90 degrees with a 3 um radius
# S 10 : straight again by 10 um
# B -90 3: bend by -90 degrees with a 3 um radius
seq = [["S",10],["B",90,3],["S",10],["B",-90,3]]

# Step 2 pass the sequence to the sequencer initializer
sequencer = BaseWaveguideSequencer(seq)

# Step 4 Run the sequencer and get the geometry
geomE += sequencer.run()

# Now, let's change some default parameters. After run, it's a good idea to reset
sequencer.reset()
sequencer.options["defaultWidth"] = 0.5 # Default is 300 nm thickness
sequencer.options["wgLayer"] = 3 # Default is layer 1
sequencer.options["bendResolution"] = 60 # Default is 30 points

g2 = sequencer.run() # Re-run the sequencer
g2.translate(30, 0) # move the waveguide up, so we can compare
geomE+=g2

### More advanced sequences
# T 2 0.5: linear taper with length of 2 um to a width of 0.5 
# T 2 -1: same as before but -1 means "go back to default width"

seq = [['S',3],['T',2,0.5],['S',2],['T',2,-1],['S',5]]
sequencer = BaseWaveguideSequencer(seq)
g3 = sequencer.run()

# Some cool stuff:
# You can gather some information about the waveguide after it has run
print(sequencer.state)
# This one should print:
#{'x': 14.0, 'y': 0.0, 'a': 0, '__OL__': 14, '__XC__': 0, '__YC__': 0, 'STORED': [], 'w': 0.3}
# x-> the final position x coordinate
# y-> final y coordinate
# a-> angle of orientation 0=east 90=north etc...
# __OL__ -> total path length
# w -> width at the end
# STORED -> a list of coordinates stored along the sequence, you need to use the "STORE" command in the sequence
# __XC__/__YC__-> position of the waveguide start point relative to the center when using the CENTER command

g3.translate(0, 30)
geomE+=g3

# Now let's go back to the previous sequence
seq = [["S",10],["B",90,3],['STORE'],["S",10],['CENTER',0,0],["B",-90,3],["DEV","BASELIB_FGC",'p1','p1']]
# We want to store the position after the first bend. 
# We also want to make the position before the second bend at coordinate [0,0]
# Finally, in the last command we insert a device at the end of the sequence
# We specify the input port 'p1' and output port to be the same port. 
# More info about devices with port on the next tutorial
sequencer = BaseWaveguideSequencer(seq)
g4 = sequencer.run()
print(sequencer.state)
# Now STORED contains [0,-10], which is relative to the new center 
# Note that subsequent translations on the geometry g4, will not alter the sequencer state
g4.translate(50, 50)
geomE+=g4


# Let's add all to main cell
themask.addToMainCell(geomE)    

# Export to GDS
themask.exportGDS()

# Finished!