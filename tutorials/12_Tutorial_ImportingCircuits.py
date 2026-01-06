"""
12_Tutorial_ImportingCircuits
"""


# This is an alternative way of creating circuits using a simple 
# text import instead of creating netlists manually.
# We will redo the same as 09_Tutorial_Circuits.py but using a 
# circuit file (see CircuitFile.txt).


# Let's import basic stuff
import samplemaker.layout as smlay # used for layout 
import samplemaker.devices as smdev # used for device function
import samplemaker.baselib.devices

# Create a simple mask layout
themask = smlay.Mask("12_Tutorial_ImportCircuits")

# To create a circuit we need to define a netlist.
# This time we use the ImportCircuit function for netlist

netlist = smdev.NetList.ImportCircuit("CircuitFile.txt", "bigger")

# as before we just create a circuit device and set the netlist    
cir2 = smdev.Circuit.build()
cir2.set_param("NETLIST", netlist)

# And out
geomE=cir2.run()


# Let's add all to main cell
themask.addToMainCell(geomE)    

# Export to GDS
themask.exportGDS()

# Finished!