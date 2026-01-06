"""
09_Tutorial_Circuits
"""


# In the last example we created a device with ports
# The device is also available in the BASELIB collection
# we will use this from now on

# Let's import basic stuff
import samplemaker.layout as smlay # used for layout 
import samplemaker.makers as sm # used for drawing
import samplemaker.devices as smdev # used for device function
import samplemaker.baselib.devices
from samplemaker.viewers import DeviceInspect

# Create a simple mask layout
themask = smlay.Mask("09_Tutorial_Circuits")

# To create a circuit we need to define a netlist:
# The netlist is built as a list of NetlistEntry objects
# Each NetlistEntry specifies a device and its connectivity
# NetListEntry(devicename, x_position,y_position, rotation, connectivity, parameters)
# The connectivity is a python dictionary that assigns each port in the device to a port name in the circuit
    
entry_list = [smdev.NetListEntry("BASELIB_DCPL", 0, 0, "E", {"p1":"inA","p4":"inB",
                                                          "p3":"AAA","p2":"BBB"}, {}),
              smdev.NetListEntry("BASELIB_FGC", -30, 0, "W", {"p1":"inA"}, {}),
              smdev.NetListEntry("BASELIB_FGC", 30, -15, "S", {"p1":"inB"}, {})]

# in the above netlist we included our DC and a grating coupler and connected left_top to in via inA
# We have not connected AAA and BBB
# Now let's make a netlist
netlist = smdev.NetList("my_circuit", entry_list)

# We can tell the netlist to align some of the ports
netlist.set_aligned_ports(["inA"])
# We need to expose AAA and BBB 
netlist.set_external_ports(["AAA","BBB"])

#Now let's create a circuit, which is also a Device and can be placed inside netlists!
cir = smdev.Circuit.build()
# We need to pass the NETLIST parameter
cir.set_param("NETLIST",netlist)

# Here we go
geomE = cir.run();

# The above device is a 2-port device with ports named AAA and BBB

################################################################################ 
#Now, let's try and instantiate two of the above circuits and connect them together
# The netlist name of the circuit is X
elist = [smdev.NetListEntry("X",0,0,"E",{"AAA":"input","BBB":"link"},{"NETLIST":netlist}),
         smdev.NetListEntry("X",40,12,"E",{"AAA":"link","BBB":"output"},{"NETLIST":netlist})]
# So we placed two of the above netlists and connected BBB of the first to AAA of the second
netlist2 = smdev.NetList("bigger",elist)

cir2 = smdev.Circuit.build()
cir2.set_param("NETLIST", netlist2)

# Now suppose we want to change the gap of the second beam splitter, how do we do that?
# Namespaces separated by ::
# in doubt you can always print(cir2._p)
cir2.set_param("dev_X_1::dev_BASELIB_DCPL_1::gap", 0.1)

c2g = cir2.run()
c2g.translate(100,0)
geomE+=c2g


###############################################################################
# We can also use circuits (or any port device) in tables and autolink
# elements between rows or columns
# let's see how

# Let's build a 1D array 
tab = smlay.DeviceTable(cir, 1, 10, {}, {})
# Specify the position (let's offset them a little bit as we move over columns)
# We do this by setting ax=30 and ay = 15
tab.set_table_positions(tab.Regular(1,10, 40, 15, 0, 0))
# Now we can auto-link columns!
tab.set_linked_ports((),(("BBB","AAA"),)) # links BBB to AAA of the next

# Let's just get the geometries from the table
tabg = tab.get_geometries()
tabg.translate(0, 100);
geomE+=tabg     

# Let's add all to main cell
themask.addToMainCell(geomE)    

# Export to GDS
themask.exportGDS()

# Finished!