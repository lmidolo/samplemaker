"""
This module contains the classes to configure the mask layout. 

Mask layout
-----------
The `Mask` class handles the layout of the structure. It should be seen as the 
main interface to the final GDS file. In essence, a Mask contains the database
of GDS cells to be exported. 

It is recommended to instantiate only a single `Mask` object in each script.
An empty GDS file can be created as follows:
    
    mask = Mask("test_mask")
    mask.exportGDS()

By default, the GDS file contains a single structure called 'CELL00'. To modify
the symbol name, change the `Mask.mainsymbol` variable. 
By default, new geometry elements should be added to the main cell with the 
`Mask.addToMainCell` method. To add more cells manually, use `Mask.addCell` instead.  
At export time, all cell references that are not referenced by the main cell are
automatically discarded.

### Cache system
To speed up script execution, it is possible to activate a cache system by 
the `Mask.set_cache` method. 

    mask.set_cache(True)

The cache uses the python `pickle` package to save the current geometry to file 
when exporting to GDS. When the script starts, if the cache is turned on and the
cache file exist, the data is loaded in memory and updated only where necessary.

Additionally, if a structure is not changed and a GDS file already exists, the 
GDS data from the previous file is loaded and copied to the output file. 

By default, the cache is disabled as for small masks with few polygons there is
no significant advantage in run time. Using the cache is highly recommended for large masks.

### Electron beam lithography and write-fields
A write-field is a square area of the design where electron-beam lithography
tools write without moving the stage. Within this area, the patterns are usually
accurately reproduced. 
When masks contain multiple write-fields, it is recommended to avoid placing 
polygons that overlap the fields, as the coarse stage motion will likely result
in so-called stitching errors. 

To help the mask design process, it is possible to define and display write-fields
in the `Mask` class. These can either be added individually or as a grid. To add
a 10x10, 500x500 um2 large write-field grid:
    
    mask.addWriteFieldGrid(500,0,0,10,10)
    
Write-fields are only used as a visual aid in `samplemaker` to assist the placement
of geoemetries in the mask.

Aligment marks
--------------

When running multiple exposures in UV or e-beam lithography, it is usually required
to place aligment marks in the layout. 
Marks are defined separately using the `Marker` and `MarkerSet` classes.
The common approach is to define a named `MarkerSet` and add it to the list of 
marker sets in the `Mask` class:
    
    markerset = MarkerSet("Ebeam1", markdev,
                x0=0,y0=0,mset=4,xdist=2000,ydist=2000)
    mask.addMarkers(markerset)
    
The above example creates a 2x2 mark set (mset=4) 2 mm apart called "Ebeam1".
The actual shape used to draw the marker is provided by the Device object "markdev"
(see `samplemaker.devices` submodule).


Devices and Device tables
-------------------------
Samplemaker features a Device creation system in the `samplemaker.devices` submodule.
It allows generating parametric drawings which can be reused and instantiated with 
different parameters. Device tables are one- or two-dimensional arrays of devices 
created by sweeping some of the parameters. 
The `DeviceTable` class helps in generating these tables without using "for" loops.
It places the devices consistently according to their bounding boxes.
Device tables are great for making parametric sweeps for e.g. lithographic tuning
of devices or testing different device property.

Additionally, it is possible to define table headers (text to be placed on the 
side of each table) to print the parameter being sweeped and its values.
This is done via the `DeviceTableAnnotations` class. 

"""

from samplemaker.makers import make_aref, make_path, make_circle, make_text
from samplemaker.shapes import GeomGroup, Box, SRef, ARef
from samplemaker.gdswriter import GDSWriter
from samplemaker.gdsreader import GDSReader
from samplemaker.devices import Device
from samplemaker import LayoutPool, _DevicePool, _DeviceCountPool, _DeviceLocalParamPool, _BoundingBoxPool
import pickle # for cacheing
from copy import deepcopy
import math

class Marker:
    """
    Class that defines a single Marker.
    """
    def __init__(self, name: str, dev: Device, x0: float = 0, y0: float = 0):      
        """
        Marker class initializer. Use this class with custom devices to place a single marker in the layout.

        Parameters
        ----------
        name : str
            Provide a string to define the mark group.
        dev : samplemaker.devices.Device
            A device object that produces a marker.
        x0 : float, optional
            Position of the marker, x-coordinate. The default is 0.
        y0 : float, optional
            Position of the marker, y-coordinate. The default is 0.

        Returns
        -------
        None.

        """
        self.name = name
        self.dev = dev
        self.x0 = x0
        self.y0 = y0
          
    def get_geom(self) -> GeomGroup:
        """
        Creates the geometry (runs the device) and places it in x0,y0

        Returns
        -------
        g : samplemaker.shapes.GeomGroup
            A geometry containing the marker.

        """
        self.dev.use_references=True
        g = self.dev.run()
        g.translate(self.x0,self.y0)
        return g
        
class MarkerSet(Marker):
    def __init__(self, name: str, dev: Device, x0: float = 0, y0: float = 0,
                 mset: int = 4, xdist: float = 1000, ydist: float =1000):
        """
        MarkerSet is a class to describe a set of markers (inherits Marker)
        

        Parameters
        ----------
        name : str
            The name of the marker set.
        dev : samplemaker.devices.Device
            A sample maker device to use for drawing the marker.
        x0 : float, optional
            Position of the marker, x-coordinate. The default is 0.
        y0 : float, optional
            Position of the marker, y-coordinate. The default is 0.
        mset : int, optional
            Number of markers (can be 1, 2 or 4). The default is 4.
        xdist : float, optional
            X-distance between two markers. The default is 1000.
        ydist : float, optional
            Y-distance between two markers. The default is 1000.

        Returns
        -------
        None.

        """
        super().__init__(name,dev,x0,y0)
        self.mset = mset
        self.xdist = xdist
        self.ydist = ydist
    
    def get_geom(self) -> GeomGroup:
        """
        Creates the geometry (runs the device) and places copies of them in the mask.

        Returns
        -------
        g : samplemaker.shapes.GeomGroup
            A geometry containing the marker.

        """
        self.dev.use_references=True
        g = self.dev.run()
        sref = g.group[0]
        if(self.mset==2):
            aref = make_aref(self.x0, self.y0, sref.cellname, sref.group, 2, 1, self.xdist, 0, 0, self.ydist)
            return aref
        
        if(self.mset==4):
            aref = make_aref(self.x0, self.y0, sref.cellname, sref.group, 2, 2, self.xdist, 0, 0, self.ydist)
            return aref
        return g

class DeviceTableAnnotations:
    def __init__(self,rowfmt: str, colfmt: str, xoff: float, yoff: float, rowvars: tuple, colvars: tuple,
                 text_width: float =1, text_height: float =10,
                 left: bool = True,right: bool =True,above: bool = True,below: bool = True):
        """
        Initalize the DeviceTableAnnotations class that controls how text is produced in tables.
        You can define headers on the four edges of a table.
        An instance of this object should be passed to `DeviceTable.set_annotations` method to 
        add headers. 

        Parameters
        ----------
        rowfmt : str
            A template string for formatting the rows text. %I and %J will be replaced
            with the row and column number, respectively. %Cn and %Rn will be replaced by
            the n-th column and row variable value, defined in rowvars and colvars. For example
            if the colvars is ("var0","var1",), the format %C0 will be replaced
            by the value of var0 on each column and %C1 will be replaced by the value of var1.
        colfmt : str
            A template string for formatting the column text. Same as rowfmt.
        xoff : float
            Distance of header text from the edge of the table in the x direction.
        yoff : float
            As xoff but in the y direction.
        rowvars : tuple
            A tuple containing a list of varable names that will change along rows.
        colvars : tuple
            Same as colvars but for columns.
        text_width : float, optional
            Width of text to be rendered. The default is 1.
        text_height : float, optional
            Size of text to be rendered. The default is 10.
        left : bool, optional
            Render header on the left side of the table. The default is True.
        right : bool, optional
            Render header on the right side of the table. The default is True.
        above : bool, optional
            Render header on top of the table. The default is True.
        below : bool, optional
            Render header on the bottom of the table. The default is True.

        Returns
        -------
        None.

        """
        self.colfmt = colfmt
        self.rowfmt = rowfmt
        self.colvars = colvars
        self.rowvars = rowvars
        self.left = left
        self.right = right
        self.above = above
        self.below = below
        self.xoff = xoff
        self.yoff = yoff
        self.text_width = text_width
        self.text_height = text_height
        self.to_poly = True

    def set_poly_text(self, to_poly: bool):
        """
        Sets whether table annotation should be rendered as polygon objects
        or text objects.

        Parameters
        ----------
        to_poly : bool
            Set this to True to render polygon text.

        Returns
        -------
        None.

        """
        self.to_poly = to_poly
    
    def render(self,i: int,j: int,rows: int,cols: int,x0: float,y0: float, rowdict: dict, coldict: dict)-> GeomGroup:
        """
        Renders the text for a given element in a table. This function should not be called
        by the user. It is intended to be run by the DeviceTable functions.

        Parameters
        ----------
        i : int
            Row index of the table.
        j : int
            Column index of the table.
        rows : int
            Number of rows.
        cols : int
            Number of columns.
        x0 : float
            X-Position of the item on the table.
        y0 : float
            Y-Position of the item on the table.
        rowdict : dict
            The dictionary associating the variables and values that change along rows.
        coldict : dict
            The dictionary associating the variables and values that change along columns.

        Returns
        -------
        samplemaker.shapes.GeomGroup
            A geometry with the annotation associated to the table element i,j.

        """
        coltxt = deepcopy(self.colfmt)
        rowtxt = deepcopy(self.rowfmt)
        coltxt = coltxt.replace("%I",str(i))
        rowtxt = rowtxt.replace("%I",str(i))
        coltxt = coltxt.replace("%J",str(j))
        rowtxt = rowtxt.replace("%J",str(j))
        for v in range(len(self.colvars)):
            pstr = "%C"+str(v)
            rval = coldict[self.colvars[v]][j]
            rval = round(rval*1000)/1000
            coltxt = coltxt.replace(pstr,str(rval))
            rowtxt = rowtxt.replace(pstr,str(rval))
        for v in range(len(self.rowvars)):
            pstr = "%R"+str(v)
            rval = rowdict[self.rowvars[v]][i]
            rval = round(rval*1000)/1000
            coltxt = coltxt.replace(pstr,str(rval))
            rowtxt = rowtxt.replace(pstr,str(rval))  
        g = GeomGroup();
        if(self.left and j==0):
            x = x0-self.xoff
            y = y0
            g+= make_text(x,y,rowtxt,self.text_height,self.text_width)
        if(self.right and j==(cols-1)):
            x = x0+self.xoff
            y = y0
            g+= make_text(x,y,rowtxt,self.text_height,self.text_width)
        if(self.above and i==(rows-1)):
            x = x0
            y = y0+self.yoff
            g+= make_text(x,y,coltxt,self.text_height,self.text_width)
        if(self.below and i==0):
            x = x0
            y = y0-self.yoff
            g+= make_text(x,y,coltxt,self.text_height,self.text_width)
        if(self.to_poly):
            g.all_to_poly()
        return g        

class DeviceTable:
    def __init__(self, dev: Device, nrow: int, ncol: int, rowvars: dict, colvars: dict):
        """
        Create a table of `samplemaker.devices.Device` objects and generate their geometries
        in an array. The array can have 1 or more rows and 1 or more columns.
        On each row and column the device will be instantiated according to the values
        provided by the rowvars and colvars parameters.
        
        Note that the actual position of the rendered devices on the table (x,y coordinate)
        is not defined here. You can use the `set_table_positions` method to control
        where each item in the table is created. 
        Alternatively, the `auto_align` method should be used to create a regularly-spaced
        table. By default `auto_align` is called upon initialization and assumes zero
        spacing between elements.

        Parameters
        ----------
        dev : samplemaker.device.Device
            The device to be instantiated in the table. The device should be already built
            via the build() command.
        nrow : int
            Number of rows (typically in y direction).
        ncol : int
            Number of columns (typically in x direction).
        rowvars : dict
            A dictionary that associates a device parameter to a list of values. 
            The list of values should have the same size as the number of rows.
            On each row the device parameter will be changed according to the values 
            listed. Multiple parameters can be swept simultaneously.
        colvars : dict
            Same as rowvars but controls the parameters being changed along columns.

        Returns
        -------
        None.

        """
        self.dev = deepcopy(dev) # A prebuilt device with preset parameters
        self.nrow = nrow
        self.ncol = ncol
        self.rowvars = rowvars
        self.colvars = colvars
        self.col_linkports= () # "Tuple of tuples containing port names that should be linked along columns")
        self.row_linkports= () # "Tuple of tuples containing port names that should be linked along rows")
        self.col_alignports = False #, "The first pair specified in col_linkports will be aligned",bool)
        self.row_alignports = False # "The first pair specified in row_linkports will be aligned",bool)
        self.device_rotation = 0
        self.annotations = None
        self.use_references = True 
        self.pos_xy =  tuple([tuple([(0,0) for i in range(ncol)]) for j in range(nrow)]) # A colsxrows tuple of coordinates for placing the elements
        self._external_ports = dict() # Stores the output ports 
        self._geometries=[]
        self._portmap=[]
        self._backup_dev = deepcopy(dev) # Keep it to reset the whole thing
        self._getgeom_ran = False
            
    def set_table_positions(self, positions: tuple):
        """
        Defines the position of each element using a 3-dimensional tuple of the 
        kind pos[i][j][k] where i,j control the row and column element and k=0,1
        are the x and y coordinate.

        Parameters
        ----------
        positions : tuple
            The tuple describing the position of each element in the table.

        Returns
        -------
        None.

        """
        self.pos_xy = positions
        self._geometries=[]
        self._portmap=[]

    def shift_table_origin(self, dx: float, dy: float):
        newpos = tuple([tuple([(dx+self.pos_xy[i][j][0],dy+self.pos_xy[i][j][1]) for j in range(self.ncol)]) for i in range(self.nrow)])
        self.set_table_positions(newpos)
        
    def set_linked_ports(self,row_linkports: tuple = (), col_linkports: tuple =()):
        """
        Automatically route ports between devices across columns and rows.

        Parameters
        ----------
        row_linkports : tuple, optional
            Tuple of tuples containing port names that should be linked along rows. The default is ().
        col_linkports : tuple, optional
            Tuple of tuples containing port names that should be linked along columns. The default is ().

        Returns
        -------
        None.

        """
        self.col_linkports=col_linkports
        self.row_linkports=row_linkports
        
    
    def set_aligned_ports(self, align_rows: bool = False, align_columns: bool = False):
        """
        Align ports along columns and rows. 

        Parameters
        ----------
        align_rows : bool, optional
            If true, the first pair specified in row_linkports will be aligned. The default is False.
        align_columns : bool, optional
            If true, the first pair specified in col_linkports will be aligned. The default is False.

        Returns
        -------
        None.

        """
        self.col_alignports = align_columns
        self.row_alignports = align_rows
        
    def set_device_rotation(self, device_rotation: float):
        """
        Rotates each device in the table.

        Parameters
        ----------
        device_rotation : float
            Angle in degrees.

        Returns
        -------
        None.

        """
        self.device_rotation=device_rotation
        self._geometries=[]
        self._portmap=[]
        
    def set_annotations(self, annotations: DeviceTableAnnotations):
        """
        Sets the table headers using the `DeviceTableAnnotations` class.

        Parameters
        ----------
        annotations : DeviceTableAnnotations
            The annotation class.

        Returns
        -------
        None.

        """
        self.annotations=annotations
        
    def get_external_ports(self) -> dict:
        """
        If the device contains ports, all the instantiated ports are returned
        so that tables can be connected to external devices or ports.

        Returns
        -------
        dict
            A dictionary of all external ports.

        """
        return deepcopy(self._external_ports)
    
    def __build_geomarray(self):
        dev = self.dev
        self._portmap = [[dict() for i in range(self.ncol)] for j in range(self.nrow)]     
        self._geometries = [[GeomGroup() for i in range(self.ncol)] for j in range(self.nrow)]
        for i in range(self.ncol):
           for var,valuelist in self.colvars.items():
               if(len(valuelist)!=self.ncol):
                   dev.set_param(var,valuelist[0])
               else:
                   dev.set_param(var,valuelist[i])   
           for j in range(self.nrow):
               for var,valuelist in self.rowvars.items():
                   if(len(valuelist)!=self.nrow):
                       dev.set_param(var,valuelist[0])
                   else:
                       dev.set_param(var,valuelist[j])
               dev.set_angle(math.radians(self.device_rotation))
               dev.use_references = self.use_references
               self._geometries[j][i]=dev.run()
               self._portmap[j][i] = deepcopy(dev._ports)
               
    def __place_portmap(self):
        # Adjusts the portmap according to the current positions
        if(self._geometries==[]):
            self.__build_geomarray()
        
        for i in range(self.ncol): 
            for j in range(self.nrow):
                geom = self._geometries[j][i]
                geom.translate(self.pos_xy[j][i][0], self.pos_xy[j][i][1])
        
                for pp in self._portmap[j][i].values():
                    pp.x0+=self.pos_xy[j][i][0]
                    pp.y0+=self.pos_xy[j][i][1]
                    #print(i,j,pp.name,pp.x0,pp.y0)
    
    def auto_align(self,min_dist_x: float, min_dist_y: float, numkey: int = 5):
        """
        Automagically aligns devices in the table according to their bounding boxes.
        The spacing is controlled by min_dist_x and min_dist_y. 

        Parameters
        ----------
        min_dist_x : float
            The distance between devices along columns.
        min_dist_y : float
            The distance between devices along rows.
        numkey : int, optional
            Selects which point of the bounding box should be aligned. Specify the
            box corner by visually matching it to the numerical keypad of standard
            keyboards (e.g. 1 is lower left corner, 3, lower-right, etc)
            The default is 5 (center).

        Returns
        -------
        None.

        """
        if(self._geometries==[]):
            self.__build_geomarray()
        
        # Get all BB (NOTE: this is slow for large devices with lots of features)
        bboxes = [[self._geometries[j][i].bounding_box() for i in range(self.ncol)] for j in range(self.nrow)]
        self.pos_xy = [[[0,0] for i in range(self.ncol)] for j in range(self.nrow)]
        # Place them according to the numkey point
        x_extrR = [-1e23 for i in range(self.ncol)]
        x_extrL = [1e23 for i in range(self.ncol)]
        y_extrT = [-1e23 for i in range(self.nrow)]
        y_extrB = [1e23 for i in range(self.nrow)]
        for i in range(self.ncol):
            for j in range(self.nrow):
                (bx,by) = bboxes[j][i].get_numkey_point(numkey)
                self.pos_xy[j][i][0]=-bx
                self.pos_xy[j][i][1]=-by
                bboxes[j][i].llx-=bx
                bboxes[j][i].lly-=by
                if(bboxes[j][i].urx()>x_extrR[i]): x_extrR[i] = bboxes[j][i].urx()         
                if(bboxes[j][i].ury()>y_extrT[j]): y_extrT[j] = bboxes[j][i].ury()
                if(bboxes[j][i].llx<x_extrL[i]): x_extrL[i] = bboxes[j][i].llx     
                if(bboxes[j][i].lly<y_extrB[j]): y_extrB[j] = bboxes[j][i].lly
        
        #print(x_extrR,x_extrL,y_extrT,y_extrB)
        
        sx = [(x_extrR[i-1]-x_extrL[i]+min_dist_x) for i in range(1,self.ncol)]
        sy = [(y_extrT[j-1]-y_extrB[j]+min_dist_y) for j in range(1,self.nrow)]
        #print(sx,sy)

        for i in range(self.ncol):
            for j in range(self.nrow):
                #print(self.pos_xy[j][i])
                if(i!=0):
                    self.pos_xy[j][i][0]+=sum(sx[0:i])
                if(j!=0):
                    self.pos_xy[j][i][1]+=sum(sy[0:j])
                #print(self.pos_xy[j][i])
                  
    
    def get_geometries(self) -> GeomGroup:
        """
        Builds the table and returns all the geometries.

        Returns
        -------
        samplemaker.shapes.GeomGroup
            The rendered table geometry

        """
        if(self._getgeom_ran):
            self._geometries = []
            self._portmap = []
            self.dev = deepcopy(self._backup_dev)
        
        if(self._geometries==[]):
            self.__build_geomarray()
        
        self.__place_portmap()
        g = GeomGroup()
        dev = self.dev
        portmap = self._portmap
        for i in range(self.ncol): 
            for j in range(self.nrow):
                geom = self._geometries[j][i]
                # The position is already set during __place_portmap()
                g+=geom
                # annotations
                if(self.annotations):
                    g+=self.annotations.render(j,i,self.nrow,self.ncol,self.pos_xy[j][i][0],self.pos_xy[j][i][1],self.rowvars,self.colvars)
                
                # Column linking
                clports = self.col_linkports
                clalign = self.col_alignports
                rlports = self.row_linkports
                rlalign = self.row_alignports
                if (i>0):
                    for links in clports:                        
                        if links[0] in portmap[j][i-1] and links[1] in portmap[j][i]:
                            p1 = portmap[j][i-1][links[0]]
                            p2 = portmap[j][i][links[1]]

                            #print(i,j,p1.x0,p1.y0,p2.x0,p2.y0)
                            if(p1.connector_function == p2.connector_function):
                                if(clalign and p1.dx() != 0 and p2.dx() != 0):
                                    ydiff = p2.y0-p1.y0
                                    geom.translate(0,-ydiff)
                                    for pp in portmap[j][i].values():
                                        pp.y0 -= ydiff    
                                                                        
                                g+=p1.connector_function(p1,p2)                                
                            else:
                                print("Warning, incompatible ports for connection between",p1.name,
                                      "and",p2.name)              
                if (j>0):
                    for links in rlports:  
                        if links[0] in portmap[j-1][i] and links[1] in portmap[j][i]:
                            p1 = portmap[j-1][i][links[0]]
                            p2 = portmap[j][i][links[1]]

                            #print(i,j,p1.x0,p1.y0,p2.x0,p2.y0)
                            if(p1.connector_function == p2.connector_function):
                                if(rlalign and p1.dy() != 0 and p2.yx() != 0):
                                    xdiff = p2.x0-p1.x0
                                    geom.translate(0,-xdiff)
                                    for pp in portmap[j][i].values():
                                        pp.x0 -= xdiff    
                                g+=p1.connector_function(p1,p2)
                            else:
                                print("Warning, incompatible ports for connection between",p1.name,
                                      "and",p2.name)             
        
                # Store external ports to expose them
                for pp in portmap[j][i].values():
                    p1 = deepcopy(pp)
                    p1.name+=f"_{j:d}_{i:d}"
                    self._external_ports[p1.name]=p1
        self._getgeom_ran = True
        return g
   
    @staticmethod
    def Regular(rows:int,cols:int,ax:float,ay:float,bx:float,by:float, x0:float = 0, y0:float = 0) -> tuple:
        """
        This static method produces a regular table array. It returns a tuple
        that can be passed to `DeviceTable.set_table_positions`.

        Parameters
        ----------
        rows : int
            Number of rows.
        cols : int
            Number of columns.
        ax : float
            x-step along rows.
        ay : float
            y-step along rows.
        bx : float
            x-step along columns.
        by : float
            y-step along columns.
        x0 : float, optional
            x-coordinate of the origin. The default is 0
        y0 : float, optional
            y-coordinate of the origin. The default is 0

        Returns
        -------
        tuple
            3-dimensional tuple of positions.

        """
        return tuple([tuple([(x0+i*ax+j*bx,y0+i*ay+j*by) for i in range(cols)]) for j in range(rows)])
    
    

class Mask:
    def __init__(self, name: str = "layout001"):
        """
        Initialize a Mask class. The name given is used as base name for file export.

        Parameters
        ----------
        name : str
            Name of the mask.

        Returns
        -------
        None.

        """
        self.name=name
        self.mainsymbol = "CELL00"
        self.writefields=[]
        self.cache=False
        self.clear()  # A new mask clears the pool
                
    def clear(self):
        """
        Clears the mask and all its content.

        Returns
        -------
        None.

        """
        LayoutPool.clear()
        _DeviceCountPool.clear()
        _DeviceLocalParamPool.clear()
        _DevicePool.clear()
        _BoundingBoxPool.clear()
        self.writefields.clear()
        self.__basic_elements()
               
    def set_cache(self, cache: bool):
        """
        Turns on or off the cache system. When cache is turned on, the layout
        is stored on disk (with .cache extension) and reloaded when the mask
        is created again (for example when running the same script multiple times).
        Addditionally, the cache system re-uses the GDS bitstream from a previously
        generated GDS file. 
        Any changes made to the devices or instances are automatically detected
        and updated even if the cache is on.
        
        This option saves a lot of time when executing scripts while making minor
        changes to the device parameters.

        Parameters
        ----------
        cache : bool
            Set to True to turn cache on.

        Returns
        -------
        None.

        """
        self.cache=cache
        if(cache):
            self.__importCache()

    def __basic_elements(self):
        # Adding a circle to the layout pool
        if "_CIRCLE" not in LayoutPool:
            c = make_circle(0, 0, 1, layer=0,to_poly=True, vertices=12)
            LayoutPool["_CIRCLE"] = c
            _BoundingBoxPool["_CIRCLE"] = Box(-1,-1,2,2)
        
    
    def addToMainCell(self,geom_group: GeomGroup):
        """
        Adds a geometry to the main cell

        Parameters
        ----------
        geom_group : samplemaker.shapes.GeomGroup
            The geometry to be added.

        Returns
        -------
        None.

        """
        if self.mainsymbol not in LayoutPool:
            LayoutPool[self.mainsymbol] = geom_group
        else:
            LayoutPool[self.mainsymbol] += geom_group
        
    def addCell(self, cellname: str, geom_group: GeomGroup):
        """
        Adds a new cell to the GDS structure and assigns a geometry to it. 

        Parameters
        ----------
        cellname : str
            The name of the cell.
        geom_group : samplemaker.shapes.GeomGroup
            The geometry to be added.

        Returns
        -------
        None.

        """
        LayoutPool[cellname] = geom_group
        
    def getCell(self, cellname: str) -> GeomGroup:
        """
        Returns a reference to the GeomGroup correspondin to the cellname.
        Note: if you modify the geometry, it will be also modified in the mask.

        Parameters
        ----------
        cellname : str
            The name of the cell.

        Returns
        -------
        GeomGroup
            Reference to the geometry group.

        """
        if cellname in LayoutPool:
            return LayoutPool[cellname]
        else:
            print("Cell named", cellname,"does not exist")
            return GeomGroup()
        
    def __exportCache(self):
        print("Storing objects in cache file")
        cachefile=open(self.name+".cache","wb")
        # Note that we do not need the full geometry, as we will just reload
        # it from the GDS file. So we keep the references only.
        # We might, however, need to re-compute the bounding boxes
        # for example in table autoalignment. Thus we replace the reference
        # groups with theyr bboxes
        #for key,val in LayoutPool.items():
        #    val.keep_refs_only()
                
            
        data = (LayoutPool,_DeviceCountPool,_DeviceLocalParamPool,_DevicePool,_BoundingBoxPool)
        pickle.dump(data,cachefile)
        cachefile.close()
        print("Done.")
        
    def __importCache(self):
        try:
            with open(self.name+".cache","rb") as cachefile:
                print("Loading cache data")
                data = pickle.load(cachefile)
                print("Done")
                for key in data[0].keys():
                    LayoutPool[key]=data[0][key]
                LayoutPool.pop(self.mainsymbol,None)
                for key in data[1].keys():
                    _DeviceCountPool[key]=data[1][key]
                for key in data[2].keys():
                    _DeviceLocalParamPool[key]=data[2][key]
                for key in data[3].keys():                
                    _DevicePool[key]=data[3][key]
                for key in data[4].keys():                
                    _BoundingBoxPool[key]=data[4][key]
        except OSError:
            pass
    
    def __cleanup_cellref(self):
        # Remove useless references
        reflist = set()
        reflist = LayoutPool[self.mainsymbol].get_sref_list(reflist)
        reflist.add(self.mainsymbol)
        
        unref=[]
        unref_hsh=[]
        for ref in LayoutPool.keys():
            if ref not in reflist:
                unref+=[ref]
       
        for ref in unref:
            LayoutPool.pop(ref,None)
        for key,value in _DevicePool.items():
            if value in unref:
                unref_hsh+=[key]
                
        for hsh in unref_hsh:
            #_DeviceCountPool.pop(hsh,None)
            _DeviceLocalParamPool.pop(hsh,None)
            _DevicePool.pop(hsh,None)
        
    
    def exportGDS(self):
        """
        Finalize the mask, perform cache operations, if any, and write to GDS.

        Returns
        -------
        None.

        """
    
        self.__cleanup_cellref()
        if(self.cache): 
            try:
                gdsr = GDSReader()
                gdsr.quick_read(self.name + ".gds")
                gdsr.celldata.pop(self.mainsymbol,None)
            except:
                pass
            
        gdsw = GDSWriter()
        gdsw.open_library(self.name + ".gds")
        if(self.cache):
            gdsw.write_pool_use_cache(LayoutPool,gdsr.celldata)
        else:
            gdsw.write_pool(LayoutPool)
        gdsw.close_library()
        if(self.cache): self.__exportCache()
    
    def importGDS(self, filename: str):
        """
        Import the full mask from GDS file.

        Parameters
        ----------
        filename : str
            name of the GDS file to read from.

        Returns
        -------
        None.

        """
        
        self.clear()
        
        reflist = set()
        mainsymbolcandidates = set()

        gdsr = GDSReader()
        gdsr.quick_read(filename)
        for cname in gdsr.celldata:
            gg = gdsr.get_cell(cname)
            self.addCell(cname, gg)
            reflist = gg.get_sref_list(reflist)
        for cname in gdsr.celldata:
            if(cname not in reflist):
                mainsymbolcandidates.add(cname)
        if len(mainsymbolcandidates)==1:
            self.mainsymbol=[i for i in mainsymbolcandidates][0]
        else:
            nsubref = 0
            for cname in mainsymbolcandidates:
                nrefs = len(LayoutPool[cname].get_sref_list())
                if(nrefs>nsubref): 
                    nsubref=nrefs
                    self.mainsymbol=cname
        # Update references after reading
        for cname in gdsr.celldata:
            for e in LayoutPool[cname].group:
                if(type(e)==SRef or type(e)==ARef):
                    e.group = LayoutPool[e.cellname]
        

        
        
        
    
    def addMarkers(self, markerset: "MarkerSet"):
        """
        Add a marker set to the mask

        Parameters
        ----------
        markerset : MarkerSet
            The MarkerSet class to be added.

        Returns
        -------
        None.

        """
        g = markerset.get_geom()
        if self.mainsymbol not in LayoutPool:
            LayoutPool[self.mainsymbol] = g
        else:
            LayoutPool[self.mainsymbol] += g
            
    def addWriteField(self, wf_size: float, x0: float, y0: float, 
                      passes: int = 1, shift: float = 0):
        '''
        Add a square writefield centered in x0,y0. 

        Parameters
        ----------
        wf_size : float
            Size in um of the writefield.
        x0 : float
            X-coordinate of the writefield center in um.
        y0 : float
            Y-coordinate of the writefield center in um.
        passes : int, optional
            Number of write-field passes, not shown in the mask. The default is 1.
        shift : float, optional
            Shift of each multi-pass writefield. The default is 0.

        Returns
        -------
        None.

        '''
        self.writefields+=[(wf_size,x0,y0,passes,shift)];

    
    def addWriteFieldGrid(self, wf_size: float, x0: float, y0:float,
                       Nx: int, Ny: int, passes: int = 1, shift: float=0):
        '''
        Create a grid Nx x Ny of writefields with given size and position.

        Parameters
        ----------
        wf_size : float
            Size in um of the writefield.
        x0 : float
            X-coordinate of the writefield center in um.
        y0 : float
            Y-coordinate of the writefield center in um.
        Nx : int
            Number of write fields in x direction.
        Ny : int
            Number of write fields in y direction.
        passes : int, optional
            Number of write-field passes, not shown in the mask. The default is 1.
        shift : float, optional
            Shift of each multi-pass writefield. The default is 0.

        Returns
        -------
        None.

        '''
        for i in range(Nx):
            for j in range(Ny):
                self.addWriteField(wf_size, i*wf_size+x0, j*wf_size+y0,passes,shift)
        
        # Adding writefields
        if(len(self.writefields)>0):
            wfs = GeomGroup()
            for wf in self.writefields:
                s = wf[0]
                x = wf[1]
                y = wf[2]
                wfpath=make_path([-s/2,s/2,s/2,-s/2,-s/2],[-s/2,-s/2,s/2,s/2,-s/2],0.1,layer=10)
                wfpath.translate(x, y)
                wfs+=wfpath
            self.addToMainCell(wfs)
        
                
    def addDeviceTable(self, device_table: DeviceTable, x0: float, y0: float, cell: str = ""):
        """
        Adds a `DeviceTable` to the layout. 

        Parameters
        ----------
        device_table : DeviceTable
            A DeviceTable object to be placed in the layout.
        x0 : float
            Controls the x position of the table center.
        y0 : float
            Controls the y position of the table center.
        cell : str, optional
            Adds the table to a named cell. The default is "" (main cell).

        Returns
        -------
        None.

        """
        geoms = device_table.get_geometries()
        bb = geoms.bounding_box()
        geoms.translate(-bb.cx()+x0,-bb.cy()+y0)
        if(cell==""):
            self.addToMainCell(geoms)
        else:
            self.addCell(cell, geoms)
            
        
                


   
