"""
11_Tutorial_LayoutAssembly
"""


# Now we will look into final assembly of the mask


# Let's import basic stuff
import samplemaker.layout as smlay # used for layout 
import samplemaker.makers as sm # used for drawing
import samplemaker.devices as smdev # used for device function
# Let's get the sample maker devices
import samplemaker.baselib.devices
# Numpy
import numpy as np

# Create a simple mask layout
themask = smlay.Mask("11_Tutorial_LayoutAssembly")

# When editing large projects, it can easily take a lot of time 
# to run the entire mask. To speed up the process you can store
# some of the generated geometry in the cache, so future runs will 
# take much less time
themask.set_cache(True) #Turns on cache

geomE = sm.GeomGroup()

# Usually we define a write-field region to place our elements
# Let's use a 2x2 grid of 500-um write fields
themask.addWriteFieldGrid(500, 0, 0, 2, 2)

# Now, it's good to place some e-beam marks
# for multi-layer alignment. A mark is available in base lib
markdev = smdev.Device.build_registered("BASELIB_CMARK")
# We can change some parameter of the marker, by default it's the e-beam marker
# We create a markerset first
markerset = smlay.MarkerSet("Ebeam1", markdev,
                x0=-200,y0=-200,mset=4,xdist=900,ydist=900)
themask.addMarkers(markerset)

# Then we proceed with the drawing of various parts 
# We could make a table of directional couplers connected to gratings
# So first we make the circuit
elist = [smdev.NetListEntry("BASELIB_DCPL", 0, 0, "E", {"p1":"in","p2":"out"},{}),
         smdev.NetListEntry("BASELIB_FGC", -25, -10, "S", {"p1":"in"},{}),
         smdev.NetListEntry("BASELIB_FGC", 25, 20, "N", {"p1":"out"},{})]
nlist = smdev.NetList("SimpleCircuit", elist)
nlist.set_aligned_ports(["in"])

cir = smdev.Circuit.build()
cir.set_param("NETLIST", nlist)

# Now we make a table of that circuit

tab = smlay.DeviceTable(cir,7, 5, 
                        {"dev_BASELIB_DCPL_1::gap":np.array([0.1,0.12,0.14,0.16,0.18,0.20,0.22])}, 
                         {"dev_BASELIB_DCPL_1::width":np.array([0.3,0.31,0.32,0.33,0.34])})
# Specify the position 
tab.set_table_positions(tab.Regular(7,5, 70, 0, 0, 50))

tabg = tab.get_geometries()
geomE+=tabg

# Note it can take a bit to compile the geometry the first time.
# But try and re-run it and make small changes with cache on!

# Let's add all to main cell
themask.addToMainCell(geomE)    

# Export to GDS
themask.exportGDS()

# Finished!
