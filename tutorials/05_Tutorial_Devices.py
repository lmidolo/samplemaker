"""
05_Tutorial_Devices
"""


# In this tutorial we look into the samplemaker device architecture.
# It allows us to create library parts that can be interconnected, iterated into tables, etc..

# Let's import basic stuff
import samplemaker.layout as smlay # used for layout 
import samplemaker.makers as sm # used for drawing
# We need the device class
from samplemaker.devices import Device
# And the device inspection tool
from samplemaker.viewers import DeviceInspect


# Create a simple mask layout
themask = smlay.Mask("05_Tutorial_Devices")

# Empty geometry
geomE = sm.GeomGroup()

# We will take as example a device called free-free membrane
# 10.1103/PhysRevB.98.155316
# We draw a rectangular membrane supported by tethers
# and use boolean operations to create the negative to be etched
# Instead of typing all code in the main script, we create a parametric device
# by deriving from the base class Device, which we imported earlier

# class definition
class FreeFreeMembrane(Device):
    # We need to implement a few mandatory functions here:
    def initialize(self):
        # This function setups some variable, like the unique identifier name
        self.set_name("CUSTOM_FFM")
        # Also add a description, useful for documenting later
        self.set_description("Free free membrane as in 10.1103/PhysRevB.98.155316, etc etc")
                
    def parameters(self):
        # define all the paramters of the device and their default values.
        # You can specify what type the parameter has and what it the minimum-maximum allowed values
        # Default is float and range (0,infinity) for all parameters.
        self.addparameter("L", 40, "Length of the membrane", param_type=float, param_range=(0.5,150))
        self.addparameter("W", 12.5, "Width of the membrane")
        self.addparameter("tetW", 2, "Tether width")
        self.addparameter("tetOff", 11, "Tether offset from the center")
        self.addparameter("R", 30, "Support ring radius")
        
    def geom(self):
        # This is where we place the commands for drawing!
        # This function should return a GeomGroup
        
        # we can fetch the parameters first to shorten the notation
        # note that you can choose whetner a type cast should be made (i.e. forcing the parameter to be
        # of the type specified in the addparameter command) and if it should be clipped in the allowed range. 
        p = self.get_params(cast_types=True,clip_in_range=True)
        # Draw the membrane
        mem = sm.make_rect(0,0,p["W"],p["L"])
        # Draw tether
        tet = sm.make_rect(0,p["tetOff"],p["R"]*2,p["tetW"])
        # Mirror to get the second one
        tet2 = tet.copy()
        tet2.mirrorY(0)
        mem+=tet+tet2
        # Support ring
        ring = sm.make_circle(0, 0, p["R"],to_poly=True,vertices=64)
        # boolean
        ring.boolean_difference(mem, 1, 1)
        return ring
        
# That's all, we now have a device that we can instantiate multiple times with diffrerent parameters!

# You can call the build method in Device to instantiate your class object
ffm_dev = FreeFreeMembrane.build()

# Before instantiating the device, we can use the DeviceInspect() command to 
# open a graphical interface to test the parameters.
# It is a good idea to move the sliders of all the parameters
# and check if the intended result is obtained.
DeviceInspect(ffm_dev)

# Now let's see how to create a geometry and add it to the main cell. 
# Now we can change parameters
ffm_dev.set_param("L",42)
# And now we can get the geometry. Use the run() command
geomE += ffm_dev.run()
# TADA! Note that the device has been automatically placed into a SREF, so you can reuse it in your code
# In the next tutorial we will see how to organize devices in collections and instantiate them in tables

# Let's add all to main cell
themask.addToMainCell(geomE)    

# Export to GDS
themask.exportGDS()

# Finished!