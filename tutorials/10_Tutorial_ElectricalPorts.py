"""
10_Tutorial_ElectricalPorts
"""


# So far we used devices with optical port connectivity
# You can create arbitrary connectors of different kind
# Here we look at the electrical connectors combined with optical connectors
# We also look how to re-use devices in other devices!

# Let's import basic stuff
import numpy as np
import samplemaker.layout as smlay # used for layout 
import samplemaker.makers as sm # used for drawing

# We take the default router from sample maker 
from samplemaker.routers import ElbowRouter

# We need the base DevicePort class
from samplemaker.devices import Device, DevicePort

from TutorialCollection import FreeFreeMembrane

# Create a simple mask layout
themask = smlay.Mask("10_Tutorial_ElectricalPorts")

# Before starting, we need to create an electrical port that we like, for example
# some global connector options
ElectricalConnectorOptions = {"elbow_offset":5,
                          "metal_layer":3}

# Then the connector function, which takes care of returning a geometry when called
def ElectricalConnector(port1: DevicePort,port2: DevicePort):
    xpts,ypts = ElbowRouter(port1, port2,ElectricalConnectorOptions["elbow_offset"])
    
    # Let's also taper the width of the connector for non-uniform port size 
    widths =np.linspace(port1.width,port2.width,len(xpts)).tolist()
    
    return sm.make_tapered_path(xpts,ypts,widths,
                        layer=ElectricalConnectorOptions["metal_layer"])
    

# Now let's create a new DevicePort with a connector function
class ElectricalPort(DevicePort):
    def __init__(self,x0: float, y0 : float,orient: str ="East",width: float =None,name: str =None):
        orient = orient.lower()
        horizontal = True
        forward = True
        if(orient=="west" or orient=="w"):
            forward=False
        if(orient=="north" or orient=="n"):
            horizontal=False
        if(orient=="south" or orient=="s"):
            horizontal=False
            forward=False
            
        super().__init__(x0,y0,horizontal,forward)
        self.width = width
        self.name=name
        self.connector_function=ElectricalConnector


# we want to reuse the FreeFreeMembrane in a device that has a local electrical connection
# So we make a new device
class FreeFreeMembraneELE(FreeFreeMembrane):
    def initialize(self):
        super().initialize() # useless in this case but always good practice
        self.set_name("CUSTOM_FFM_E")
        self.set_description("Electrified version of the free free membrane")
    
    def parameters(self):
        super().parameters() # Inherit all parameters
        self.addparameter("mesawidth", self._p["R"]*2+20, "The size of the mesa")
    
    def geom(self):
        g = super().geom() # Get the membrane first
        # Now we draw a mesa around it.
        S = self._p["mesawidth"]
        # Draw the mesa area as a filled polygon, here a simple square
        mesa = sm.make_rect(0,0,S,S)
        
        conn_w = 0.8
        port1 = ElectricalPort(0, S/2, "north", conn_w, "emesa")
        # and add it to local port
        self.addlocalport(port1)
                
        # Now draw a metal pad and wire to the port (again we use fixed values, could be parametrized)
        pad=sm.make_rounded_rect(0, S/2-5, S-10, 4, 1)
        pad += sm.make_path([0,0],[S/2-5,S/2],conn_w,to_poly=True)
        pad.set_layer(ElectricalConnectorOptions["metal_layer"])
        pad.boolean_union(ElectricalConnectorOptions["metal_layer"])

        g+=mesa+pad
        return g

# To test it, let's create two and connect them!
ffme1 = FreeFreeMembraneELE.build()
geomE = ffme1.run()

ffme2 = FreeFreeMembraneELE.build()
ffme2._x0 = 100 # Note this is usually not recommended, use netlist to place objects!
geomE += ffme2.run()

#using the connector function of the port, see tutorial 9
conn_fun=ffme1._ports["emesa"].connector_function
geomE += conn_fun(ffme1._ports["emesa"],ffme2._ports["emesa"])

# Let's add all to main cell
themask.addToMainCell(geomE)    

# Export to GDS
themask.exportGDS()

# Finished!
