"""
08_Tutorial_WaveguideDevices
"""


# In this tutorial we create a simple directional coupler
# as a Device that can be re-used in circuits.

# Let's import basic stuff
import numpy as np
import samplemaker.layout as smlay # used for layout 

# We need the device class
from samplemaker.devices import Device
# And the device inspection tool
from samplemaker.viewers import DeviceInspect

from samplemaker.baselib.waveguides import BaseWaveguideSequencer, BaseWaveguidePort # Used for the sequencer

# We have imported the BaseWaveguidePort, which can be used to build ports 
# interfacing the device to the outside (e.g. to other devices in a circuit).

# Create a simple mask layout
themask = smlay.Mask("08_Tutorial_WaveguideDevices")

# As in tutorial 05, let's create a device

# class definition
class DirectionalCoupler(Device):
    def initialize(self):
        self.set_name("DCPL")
        self.set_description("Simple symmetric directional coupler")
    
    def parameters(self):
        self.addparameter("length", 20, "Coupling length",float)
        self.addparameter("width", 0.3, "Width of the waveguides in the coupling section",float,(0.01,1))
        self.addparameter("gap", 0.5, "Distance between waveguides in the coupling section", float)
        self.addparameter("input_dist", 5, "Distance between waveguides at input", float,(0.01,np.inf))
        self.addparameter("input_len", 7, "Length of the input section from input to coupling", float, (3,np.inf))        
        
    def geom(self):
        p = self.get_params();
        # Draw the upper arm, then mirror
        off = p["input_dist"]/2
        clen = (p["input_len"]-1)/2
        Ltot = p["length"]+p["input_len"]*2
        seq = [['T',1,p["width"]],["C",-off,clen],
                ['S',p["length"]/2]]
        ss =  BaseWaveguideSequencer(seq)
        dc = ss.run()
        dc2 = dc.copy()
        dc2.mirrorX(Ltot/2)
        dc+=dc2
        dc.translate(-Ltot/2, off+p["gap"]/2+p["width"]/2)
        dc3 = dc.copy()
        dc3.mirrorY(0)
        dc+=dc3        
        
        # Ok, now we have to tell the device that there are 4 ports and we should 
        # define their position, size and orientation in the device frame
        # To do that, we need the information in the 2 state variables saved earlier
        # Use addlocalport() when drawing ports inside the geom() function:
   
        # In this version of sample maker ports can only be oriented north, south, east or west
        XP = Ltot/2
        YP = off+p["gap"]/2+p["width"]/2
    
        self.addlocalport(BaseWaveguidePort(-XP, YP, "west", ss.options["defaultWidth"], "p1"))
        self.addlocalport(BaseWaveguidePort( XP, YP, "east", ss.options["defaultWidth"], "p2"))
        self.addlocalport(BaseWaveguidePort(-XP,-YP, "west", ss.options["defaultWidth"], "p3"))
        self.addlocalport(BaseWaveguidePort( XP,-YP, "east", ss.options["defaultWidth"], "p4"))
        
        return dc


sdc = DirectionalCoupler.build()
geomE = sdc.run()        

# We can inspect the device
DeviceInspect(sdc)

# We will now check if ports are working as expected
# we can only connect two ports from the same device 
conn_fun = sdc._ports["p1"].connector_function; # we use this to get the connector function for the port
geomE+=conn_fun(sdc._ports["p1"],sdc._ports["p2"]) # connect two ports

# Let's add all to main cell
themask.addToMainCell(geomE)    

# Export to GDS
themask.exportGDS()

# Finished!