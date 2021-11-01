# -*- coding: utf-8 -*-
"""
Tutorial device collection

"""

# This is how you create a collection of devices, just add all the classes in this file
# Check the end of this file, we run a command to make samplemaker aware of our devices

import samplemaker.makers as sm # used for drawing
from samplemaker.devices import Device, registerDevicesInModule # We need the registerDevicesInModule function
# We import the OpticalConnectorOptions, which are global and the OpticalPort
#from samplemaker.quantumphotonics.waveguides import SuspendedWaveguideSequencer, OpticalConnectorOptions
# We also import the optical port
#from samplemaker.quantumphotonics.qpdev import OpticalPort
# Electrical options and ports/methods
#from samplemaker.quantumphotonics.electrical import ElectricalConnectorOptions, ElectricalPort_PType, make_mesa_plug, make_mesa_trench

# class definition
class FreeFreeMembrane(Device):
    # We need to implement a few mandatory functions here:
    def initialize(self):
        # This function setups some variable, like the unique identifier name
        self._name="CUSTOM_FFM"
        # Also add a description, useful for documenting later
        self._description="Free free membrane as in 10.1103/PhysRevB.98.155316, etc etc"
                
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

# ### The following device is created in tutorial 09
# class SimpleDirectionalCoupler(Device):
#     def initialize(self):
#         self._name="CUSTOM_DC"
#         self._description="Basic and over-simplified directional coupler"

#         # Let's create our own sequencer
#         self._seq = SuspendedWaveguideSequencer([])      
#         # The following is required to tell the device that we will be using the optical ports
#         # The optical connector options are global and control all the sequencer options
#         self._seq.options = OpticalConnectorOptions["sequencer_options"]
#         # For this device we want to deactivate the automatic tether
#         #self._seq.options[]
                
#     def parameters(self):
#         # define all the paramters of the device, these can be short and local only
#         self.addparameter("gap", 0.15, "Distance between waveguides")
#         self.addparameter("L", 15, "Length of the coupling region")
#         self.addparameter("cw", 0.22, "Waveguide width at the coupling region")
       
        
#     def geom(self):
#         p = self._p;
#         # Before we do anything, what is the waveguide width?
#         # Let's take it from the sequencer and optical connector options...
#         inw = self._seq.state["w"]
#         # We adapt the code from tutorial 08:
#         # First waveguide
#         seqA = [["T",1,p["cw"]],["S",p["L"]/2+5],["CENTER",0,0],["S",p["L"]/2+5],["T",1,-1]]
        
#         # The second waveguide
#         seqB = [["STATE","a",90],["S",3],['T',1,p["cw"]],
#                 ['B',-90,3],["S",p["L"]/2],["CENTER",0,-p["gap"]-p["cw"]],["S",p["L"]/2],["B",-90,3],
#                 ["T",1,-1],["S",3]]
#         # We have removed the gratings, as we want to connect this to an external structure
#         # The biggest difference now is that the Device class has its own sequencer object
#         # we simply have to set the sequence
#         self._seq.seq = seqA;
#         self._seq.reset()
#         wg1 = self._seq.run()
#         stateA = self._seq.get_state(); # We store this info for later
        
#         self._seq.seq = seqB;
#         self._seq.reset()
#         wg2 = self._seq.run()
#         stateB = self._seq.get_state(); 
        
#         merged = self._seq.merge_output(wg1, wg2)
        
#         # Ok, now we have to tell the device that there are 4 ports and we should 
#         # define their position, size and orientation in the device frame
#         # To do that, we need the information in the 2 state variables saved earlier
#         # Careful! do not use addport() but addlocalport() when drawing ports inside the geom() function:
   
#         # In this version of sample maker ports can only be oriented north, south, east or west
#         # Two booleans are passed, the first is horizontal (true) or vertical(false)
#         # The second is forward(true) or backward(false)
#         # EAST: true true
#         # West: true false
#         # north: false true
#         # south: false false
#         # The first port is the upper left one and faces west
#         self.addlocalport(OpticalPort(stateA["__XC__"],stateA["__YC__"],True,False,inw,"left_top"))
#         self.addlocalport(OpticalPort(stateA["x"],stateA["y"],True,True,inw,"right_top"))
#         self.addlocalport(OpticalPort(stateB["__XC__"],stateB["__YC__"],False,False,inw,"left_bot"))
#         self.addlocalport(OpticalPort(stateB["x"],stateB["y"],False,False,inw,"right_bot"))
        
#         return merged

# # The following class is explained in tutorial 11
# class FreeFreeMembraneELE(FreeFreeMembrane):
#     def initialize(self):
#         super().initialize() # useless in this case but always good practice
#         self._name = "CUSTOM_FFM_E"
#         self._description = "Electrified version of the free free membrane"
    
#     def parameters(self):
#         super().parameters() # Inherit all parameters
#         self.addparameter("mesawidth", self._p["R"]*2+20, "The size of the mesa")
    
#     def geom(self):
#         g = super().geom() # Get the membrane first
#         # Now we draw a mesa around it.
#         S = self._p["mesawidth"]
#         # Draw the mesa area as a filled polygon, here a simple square
#         mesa = sm.make_rect(0,0,S,S)
        
#         # Then we create the trench around the mesa, use an utility for that called, make_mesa_trench
#         tw = ElectricalConnectorOptions["PType_trench_width"]  # we could of course make this a local parameter as well
#         tlay = ElectricalConnectorOptions["PType_trench_layer"] # also could be custom in a device
#         trench = make_mesa_trench(mesa,tw,tlay)
       
#         # Now we need a plug in the trench, we use the make_mesa_plug utility, which carves a port into the mesa
#         # Let's define the port straight away
#         # A connector width, can be custom:
#         conn_w = 0.8
#         port1 = ElectricalPort_PType(0, S/2, False, True, conn_w, "emesa")
#         # and add it to local port
#         self.addlocalport(port1)
#         # now we make the plug
#         trench = make_mesa_plug(trench,port1,tlay)
#         # We can repoeat this if we have more ports!
        
#         # Now draw a metal pad and wire to the port (again we use fixed values, could be parametrized)
#         pad=sm.make_rounded_rect(0, S/2-5, S-10, 4, 1)
#         pad += sm.make_path([0,0],[S/2-5,S/2],conn_w,to_poly=True)
#         pad.set_layer(ElectricalConnectorOptions["PType_metal_layer"])
#         pad.boolean_union(ElectricalConnectorOptions["PType_metal_layer"])

#         g+=trench+pad
#         return g



### Important: register all devices in this module
registerDevicesInModule(__name__)