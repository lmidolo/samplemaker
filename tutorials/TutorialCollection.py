"""
Tutorial device collection

"""

# This is how you create a collection of devices, just add all the classes in this file
# Check the end of this file, we run a command to make samplemaker aware of our devices

import samplemaker.makers as sm # used for drawing
from samplemaker.devices import Device, registerDevicesInModule # We need the registerDevicesInModule function

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


### Important: register all devices in this module
registerDevicesInModule(__name__)