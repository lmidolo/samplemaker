# -*- coding: utf-8 -*-
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
# Let's draw them in layer 10. We can also disable drawing the WFs by setting layer=-1
themask.addWriteFieldGrid(500, 0, 0, 2, 2,layer=10)

# Now, it's good to place some e-beam marks
# for multi-layer alignment. A mark is available in base lib
markdev = smdev.Device.build_registered("BASELIB_CMARK")
# We can change some parameter of the marker, by default it's the e-beam marker
# We create a markerset first
markerset = smlay.MarkerSet("Ebeam1", markdev,
                x0=-200,y0=-200,mset=4,xdist=900,ydist=900)
themask.addMarkers(markerset)

# We can fetch the writefield information as dictionary for post-processing
fieldsInfo = themask.getFieldsInfo()
# and we can fetch the markers information from the marker set
markInfo = markerset.getMarkerInfo()

# For Beamfox/Elionix users: this can be turned into metadata for SCON conversion
layoutInfo = {"size":500,"dots":1000000, "pitch":{"scan":4, "feed":4}, "fields": fieldsInfo, "marks":markInfo}
# Uncomment the following for Beamfox YAML file
# import yaml
# with open("11_Tutorial_LayoutAssembly_ldata.yaml", "w") as f:
#     yaml.dump(layoutInfo,f)

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
