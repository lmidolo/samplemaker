"""
Shape classes supported by the GDS format and most lithography systems / pattern generators.

Basic shapes in `samplemaker`
-----------------------------

The following GDS shapes are provided:

* `Poly`: closed curve polygon (GDS BOUNDARY element).
* `Path`: open curve polyline with given width (GDS PATH element).
* `Text`: text object for annotations (GDS TEXT element).
* `SRef`: reference to a single cell (GDS SREF element).
* `ARef`: array of reference to cells (GDS AREF element).

Additionally, the following non-GDS shapes are available:
    
* `Circle`: defined by center and radius.
* `Ellipse`: ellipses with rotation.
* `Ring`: elliptical or circular rings.
* `Arc`: like rings but covering a sector angle only.

Two more objects `Dot` and `Box` are available but not drawable.
They are sometimes useful for calculations
(e.g. bounding boxes or point transformations).

All the above classes (except for `SRef` and `ARef`) implement a `to_polygon` method
to convert all shapes back to GDS-exportable polygons and contain a `layer` information. 
In practice, the above classes are never needed. The shapes are created using
the functions provided in the `samplemaker.makers` submodule and manipulated with the 
`GeomGroup` class methods.

The `GeomGroup` object
----------------------

The most important class defined in the `samplemaker.shapes` module is the `GeomGroup`
class. It is an object the represents a drawing as a collection of the basic shapes
listed above. `GeomGroup` objects can be combined together, moved, scaled, and manipulated.
Additionally, several boolean operations are provided. 

### Operations on `GeomGroup`
Some methods perform operations directly on the object from which they are called.
Boolean functions are an example of methods that modify the current object.
Other methods return a copy of the object without modifying it, for example the `GeomGroup.flatten` 
method. It is recommended to check the reference of each command to understand the function behavior.

When assigning an object to another one, a shallow copy is made, so that the copied object
and the source object still refer to the same geometry. To perform a deep copy, use 
the method `GeomGroup.copy` instead:
    
    g1 = GeomGroup()
    g2 = g1 # Now both g1 and g2 refer to the same object 
    g2.set_layer(3) # Both g1 and g2 have changed layer to 3
    g3 = g1.copy() # g3 is now a separate (deep) copy of g1.
    g3.set_layer(4) # Only g3 is set to layer 4.
    
In combining multiple geometries, it is often convenient to perform shallow copies
to save memory and computation time. For example

    geomA += geom2 # Shallow copy of geom2 into geomA. Any change to geom2 will affect geomA
    geomB += geom2.copy() # Deep copy, any change to geom2 will not affect geomB


"""

import pathlib
import numpy as np
from copy import deepcopy
import math
import samplemaker.resources.boopy as boopy
from samplemaker import _BoundingBoxPool

_glyphs = dict()

_STENCIL_FONT_FILENAME = "sm_stencil_font.txt"
_STENCIL_FONT_ENCODING = "ISO-8859-1"
_STENCIL_FONT_PATH = pathlib.Path(__file__).parent / "resources" / _STENCIL_FONT_FILENAME

class GeomGroup:
    def __init__(self):
        """
        Create an empty GeomGroup with no elements

        Returns
        -------
        None.

        """
        self.group = list();
    
    def __add__(self,other : 'GeomGroup') -> 'GeomGroup':
        """
        Combines two geometries

        Parameters
        ----------
        other : 'GeomGroup'
            The GeomGroup you want to add.

        Returns
        -------
        gg : 'GeomGroup'
            The resulting GeomGroup.

        """
        gg = GeomGroup()
        gg.group = self.group + other.group
        return gg
    
    def add(self,geom):
        """
        Adds a shape to the group (deprecated)

        Parameters
        ----------
        geom : Any geometry object
            The geometry to be added.

        Returns
        -------
        None.

        """
        self.group.append(geom)
        
    def copy(self) -> "GeomGroup":
        """
        Makes a deep copy of the object.

        Returns
        -------
        GeomGroup
            A detached copy of self.

        """
        return deepcopy(self)
    
    def flatten(self, layer_list: list[int] = []) -> "GeomGroup":
        """
        Flattens the entire group. Turns all SREF and AREF objects in flattened objects.
        All references to cell are removed. A new flattened group is returned and no 
        changes are made to the calling object.

        Parameters
        ----------
        layer_list : list[int], optional
            A list of layers that should be used when flattening. The default is [] (=all).

        Returns
        -------
        g : GeomGroup
            A detached copy of the flattened geometry.

        """
        g = GeomGroup()
        if len(layer_list) == 0:
            for geom in self.group:            
                if(type(geom)==SRef or type(geom)==ARef):
                    flatg=geom.group.flatten()
                    flatg=geom.place_group(flatg)
                    g+=flatg
                else:
                    g.add(deepcopy(geom))
        else:
            for geom in self.group:            
                if(type(geom)==SRef or type(geom)==ARef):
                    flatg=geom.group.flatten(layer_list)
                    flatg=geom.place_group(flatg)
                    g+=flatg
                else:
                    if(geom.layer in layer_list):
                        g.add(deepcopy(geom))
        return g
    
    def get_sref_list(self, sref_list=set()):
        """
        Returns a unique list of strings with the 
        structures referenced by the object (recursively).

        Parameters
        ----------
        sref_list : set, optional
            A set of strings with cell names. The default is an empty set.

        Returns
        -------
        sref_list : set
            The complete reference list.

        """
        for geom in self.group:
            if(type(geom)==SRef or type(geom)==ARef):
                sref_list.add(geom.cellname)
                sref_list=geom.group.get_sref_list(sref_list)
        return sref_list                
        
    def get_layer_list(self, layer_list=set()) -> set:
        """
        Returns a unique set of int with the layers in the object (recursively)
        Should be called by the user without arguments, when querying the layers

        Parameters
        ----------
        layer_list : set, optional
            A set of integers with layers. The default is empty set.

        Returns
        -------
        layer_list: set
            The complete layer list.

        """
        for geom in self.group:
            if(type(geom)==SRef or type(geom)==ARef):
                layer_list=geom.group.get_layer_list(layer_list)
            else:
                layer_list.add(geom.layer)
        
        return layer_list                
    
    def translate(self,dx: float,dy: float):
        """
        Shifts the entire geometry by dx and dy.

        Parameters
        ----------
        dx : float
            Shift in x direction.
        dy : float
            Shift in y direction.

        Returns
        -------
        Reference to the the object.

        """
        for geom in self.group:
            geom.translate(dx,dy)
        return self
    
    def rotate_translate(self, dx: float, dy: float, rot: float):
        """
        First rotate around 0,0 and then translate by dx,dy. 
        It is typically 
        faster than using rotate() followed by translate()

        Parameters
        ----------
        dx : float
            Shift in x direction.
        dy : float
            Shift in y direction.
        rot : float
            Rotation angle in degrees.

        Returns
        -------
        Reference to the the object.

        """
        for geom in self.group:
            geom.rotate_translate(dx,dy,rot)
        return self
    
    def rotate(self,x0: float,y0: float,rot: float):
        """
        Rotates the geometry around x0,y0 by a given angle.

        Parameters
        ----------
        x0 : float
            x-coordinate of center of rotation.
        y0 : float
            y-coordinate of center of rotation.
        rot : float
            rotation angle in degrees.

        Returns
        -------
        Reference to the the object.

        """
        for geom in self.group:
            geom.rotate(x0,y0,rot)
        return self
    
    def scale(self,x0: float,y0: float,scale_x: float,scale_y: float):
        """
        Scales the geometry using x0,y0 as center

        Parameters
        ----------
        x0 : float
            x-coordinate of center of scaling.
        y0 : float
            y-coordinate of center of scaling.
        scale_x : float
            scaling factor in x direction.
        scale_y : float
            scaling factor in y direction.

        Returns
        -------
        Reference to the the object.

        """
        for geom in self.group:
            geom.scale(x0,y0,scale_x,scale_y)
        return self
    
    def mirrorX(self,x0: float):
        """
        Mirrors the geometry around x-axis

        Parameters
        ----------
        x0 : float
            x-coordinate of the mirroring axis.

        Returns
        -------
        Reference to the the object.

        """
        for geom in self.group:
            geom.mirrorX(x0)
        return self

    def mirrorY(self,y0: float):
        """
        Mirrors the geometry around y-axis

        Parameters
        ----------
        y0 : float
            y-coordinate of the mirroring axis.

        Returns
        -------
        Reference to the the object.

        """
        for geom in self.group:
            geom.mirrorY(y0)
        return self
    
    def __entity_count(self, recursive: bool = True, layer_wise: bool = False, layer:int = 0) -> dict:
        cnt = dict()
        lfgroup = self.group
        if(layer_wise):
            lfgroup = [g for g in self.group if g.layer==layer]        
        cnt["NPoly"] = len([g for g in lfgroup if type(g)==Poly])
        cnt["NPath"] = len([g for g in lfgroup if type(g)==Path])
        cnt["NText"] = len([g for g in lfgroup if type(g)==Text])
        cnt["NCircle"] = len([g for g in lfgroup if type(g)==Circle])
        cnt["NEllipse"] = len([g for g in lfgroup if type(g)==Ellipse])
        cnt["NRing"] = len([g for g in lfgroup if type(g)==Ring])
        cnt["NArc"] = len([g for g in lfgroup if type(g)==Arc])
        if not recursive:
            cnt["NSRef"] = len([g for g in self.group if type(g)==SRef])
            cnt["NARef"] = len([g for g in self.group if type(g)==ARef])
        else:
            for g in self.group:
                if type(g)==SRef or type(g)==ARef:
                    subcnt = g.group.__entity_count(recursive,layer_wise,layer)
                    if type(g)==ARef:
                        for e in subcnt.keys(): 
                            subcnt[e]*=g.ncols*g.nrows
                    for name in cnt:
                        cnt[name]+=subcnt[name]
        return cnt
    
    def __str__(self):
        """
        Display basic geometry information (size and layers)

        Returns
        -------
        msg : str
            A string with the basic information about the geometry.

        """
        bb = self.bounding_box()
        w = float(round(bb.width*1e3))/1e3
        h = float(round(bb.height*1e3))/1e3
        msg = "GeomGroup ("+str(w)+" x "+str(h)+")\n"
        msg+= "Layers: "+str(self.get_layer_list())+"\n"
        return msg
    
    def info(self) -> dict:
        """
        Generate useful statistics on the group (element count, size)
        and return it in a dict. 

        Returns
        -------
        dict
            Contains information on the group geometry.

        """
        stat = dict()
        bb = self.bounding_box()
        layer_list = self.get_layer_list()
        stat["BoundingBox"]={"x":bb.cx(),"y":bb.cy(),"width":bb.width, "height":bb.height}
        stat["LayerList"]=[l for l in layer_list]
        for l in layer_list:
            cnt = self.__entity_count(True, True, l)   
            cnt = {k: v for k, v in cnt.items() if v != 0}
            stat["Layer"+str(l)] = cnt
        cnt = self.__entity_count(True)
        cnt = {k: v for k, v in cnt.items() if v != 0}
        stat["TotalCount"] = cnt
        return stat
    
    def bounding_box(self) -> 'Box':
        """
        Calculates the group bounding box

        Returns
        -------
        bb : Box
            The box representing the bounding box of the geometry.

        """
        if len(self.group)!=0:
            bb = self.group[0].bounding_box()
            
        for geom in self.group:
            bb.combine(geom.bounding_box())
        return bb
    
    def to_boxes(self, layer: int) -> 'GeomGroup':
        """
        Generates a GeomGroup with the bounding boxes of each individual 
        geometry. It can be used to create a coarse overlay mask. Acts
        on a single layer.

        Parameters
        ----------
        layer : int
            The layer to use for bounding boxes.

        Returns
        -------
        'GeomGroup'
            A geometry group with the bounding boxes of each element in the 
            original group.

        """
        bb = GeomGroup()
        for geom in self.group:
            if(geom.layer==layer):
                bb+=geom.bounding_box().toRect()
        bb.set_layer(layer)
        return bb
            
    def set_layer(self,layer: int):
        """
        Assigns a new layer to all the shapes in the geometry

        Parameters
        ----------
        layer : int
            The new layer to be assigned.

        Returns
        -------
        Reference to the the object.

        """
        for geom in self.group:
            geom.layer=layer
        return self
            
    
    def select_layer(self,layer: int) -> 'GeomGroup':
        """
        Create a new GeomGroup containing only shapes in a given layer.

        Parameters
        ----------
        layer : int
            The selected layer.

        Returns
        -------
        g : GeomGroup
            A new GeomGroup object with elements of the selected layer.

        """
        g = GeomGroup()
        for geom in self.group:
            if(geom.layer==layer):
                g.add(geom)
        return g
    
    def select_layers(self,layers: list[int]) -> 'GeomGroup':
        """
        Create a new GeomGroup containing only shapes in a list of layers.

        Parameters
        ----------
        layers : list[int]
            The selected layer list.

        Returns
        -------
        g : GeomGroup
            A new GeomGroup object with elements of the selected layer list.

        """
        g = GeomGroup()
        for geom in self.group:
            if(geom.layer in layers):
                g.add(geom)
        return g
    
    def deselect_layers(self, layers: list[int])-> 'GeomGroup':
        """
        Create a new GeomGroup containing only shapes that are not in layer list

        Parameters
        ----------
        layers : list[int]
            A list of layer to deselect.

        Returns
        -------
        g : GeomGroup
            A new GeomGroup object without elements of the selected layer.

        """
        g = GeomGroup()
        for geom in self.group:
            if(geom.layer not in layers):
                g.add(geom)
        return g
        
    def select(self, query_str: str)-> 'GeomGroup':
        """
        Performs a selection of the shapes (filtering) based on geometrical 
        properties. The output GeomGroup contains only the elements that satisfy
        the conditions expressed in the query string.
        For example, to select only polygons with area smaller than 1, do
        sel = geom.select("A<=1").
        The geometry is flattened prior to selection if sub-references are encountered.
        The following properties can be used
            "A": Area
            "P": Perimeter
            "W": Bounding box width
            "H": Bounding box height
            "L": Layer
            "T": type (can be Poly, Path, Text, Circle, Ellipse, Ring, Arc)
            "x": centroid x coordinate
            "y": centroid y coordinate
            "llx": lower-left x coordinate of the bounding box
            "lly": lower-left y coordinate of the bounding box
            "urx": upper-right x coordinate of the bounding box
            "ury": upper-right y coordinate of the bounding box
        Any Python logical expression can be used including mathematical operations between 
        variables, for example the shape index lower than 0.2 can be queried as follows
        sel = geom.select("12.566*A/P**2<=0.2").
        
        Boolean operation should be expressed using parenthesis and bitwise operator &,^,|,!
        for example
        sel = geom.select("(x<1) & (y>5)").
        

        Parameters
        ----------
        query_str : str
            A string defining the selection condition.

        Raises
        ------
        NameError
            If variable names are not recognized.

        Returns
        -------
        'GeomGroup'
            A geometry group containing the elments that satisfy the criteria.

        """
        allowed_names = {'A': "Polygon area",
                         'P': "Polygon perimeter",
                         'W': "Bounding box width",
                         'H': "Bounding box height",
                         'L': "Layer",
                         'T': "Type",
                         'x': "X position, center or reference pos",
                         'y': "Y position, center or reference pos",
                         'llx': "lower left x position of the bb",
                         'lly': "lower left y position of the bb",
                         'urx': "upper right x position of the bb",
                         'ury': "upper right y position of the bb"}
        code = compile(query_str,"<string>","eval")
        sflat = self
        if(len(self.get_sref_list())!=0):
           sflat=self.flatten()
        # Pre-allocate Bounding boxes
        bbs = [g.bounding_box() for g in sflat.group]
        for name in code.co_names:
            if(name not in allowed_names):
                raise NameError(f"Use of expression {name} not allowed")
        
            # Prepare the local variable dictionary
            
            if name=="A": # Prepare area array
                allowed_names[name]=np.array([g.area() for g in sflat.group])
            if name=="P": # Prepare area array
                allowed_names[name]=np.array([g.perimeter() for g in sflat.group])
            if name=="L": # Prepare layer array
                allowed_names[name]=np.array([g.layer for g in sflat.group])
            if name=="W": # Prepare width array
                allowed_names[name]=np.array([b.width for b in bbs])
            if name=="H": # Prepare height array
                allowed_names[name]=np.array([b.height for b in bbs])
            if name=="x" or name=="y": # Prepare centroid array
                allowed_names["x"]=np.array([g.centroid()[0] for g in sflat.group])
                allowed_names["y"]=np.array([g.centroid()[1] for g in sflat.group])
            if name=="llx": # Prepare LL array
                allowed_names["llx"]=np.array([b.llx for b in bbs])
            if name=="lly": # Prepare LL array
                allowed_names["lly"]=np.array([b.lly for b in bbs])
            if name=="urx": # Prepare UR array
                allowed_names["urx"]=np.array([b.urx() for b in bbs])
            if name=="ury": # Prepare UR array
                allowed_names["ury"]=np.array([b.ury() for b in bbs])            
            if name=="T": # Prepare type array
                allowed_names[name]=np.array([str(g.__class__.__name__) for g in sflat.group])
            
                
        # Now execute
        g = GeomGroup()
        sel = eval(code, {"__builtins__": {}}, allowed_names)
        g.group[:] = [sflat.group[i] for i,val in enumerate(sel) if val]
        return g
       
    def find_matching_patterns(self, pattern: "GeomGroup", layer: int):        
        """
        Finds the position of a given repeating pattern in the geometry.
        User provides a pattern as a geom group. The pattern should not be 
        disjoint (i.e. after boolean union, it should contain one element only)
        The code search for the identical pattern in the whole group for a given
        layer. Once found, an array of x,y coordinates is returned, corresponding
        to coordinates of the pattern.
        Note, the code performs boolean union on the input pattern as well as
        on the entire geometry.

        Parameters
        ----------
        pattern : "GeomGroup"
            The pattern to be searched. Must be a single connected polygon
        layer : int
            The layer to perform the search on.

        Returns
        -------
        res : list
            A list of coordinate pairs, corresponding to the location of the pattern.

        """
        psearch=pattern.copy()
        psearch.all_to_poly()
        psearch.boolean_union(layer)
        if(len(psearch.group)!=1):
            print("It is only possible to search for a single polygon shape")
        plook = self.copy().boolean_union(layer)
        b1 = psearch.bounding_box()
        psearch.translate(-b1.cx(),-b1.cy())
        g2 = psearch.group[0]
        res = []
        for g in plook.group:
            if(type(g)==Poly):
                bb=g.bounding_box()
                g.translate(-bb.cx(),-bb.cy())
                if(g.identical_to(g2)):
                     res+=[[bb.cx(),bb.cy()]]   
        return res
        
            
    def get_area(self)->float:
        """
        Calculates the total area of the group

        Returns
        -------
        float
            The total area of the group.

        """
        area = 0
        for i in range(len(self.group)):
            if(type(self.group[i])==SRef or type(self.group[i])==ARef):
                area+=self.group[i].group.get_area(); 
            else:
                area+=self.group[i].area()
        return float(round(area*1e6))/1e6
    
    def path_to_poly(self):
        """
        Converts all path objects in the current group to polygons

        Returns
        -------
        None.

        """
        paths = GeomGroup()
        for i in range(len(self.group)):
            if(type(self.group[i])==Path):
                paths+=self.group[i].to_polygon()
        
        self.group[:] = [g for g in self.group if not type(g)==Path]
        self.group = self.group+paths.group
        
    def text_to_poly(self):
        """
        Converts all text objects in the current group to polygons

        Returns
        -------
        None.

        """
        polys = GeomGroup();
        for i in range(len(self.group)):
            if(type(self.group[i])==Text): 
                polys+=self.group[i].to_polygon()                

        self.group[:] = [g for g in self.group if not type(g)==Text]
        self.group = self.group+polys.group

    def all_to_poly(self, Npts_circ: int=12, Npts_arc: int=32, split_arc: bool =False ):
        """
        Converts all elements except for SRef and Aref to polygons

        Returns
        -------
        None.

        """
        
        polys = GeomGroup();
        for i in range(len(self.group)):
            g = self.group[i]
            if(type(g)==Poly):
                polys+=self.group[i].to_polygon()
            if(type(g)==Text):
                polys+=self.group[i].to_polygon()
            if(type(g)==Path):
                polys+=self.group[i].to_polygon()                
            if(type(g)==Circle):
                polys+=self.group[i].to_polygon(Npts_circ)
            if(type(g)==Ellipse):
                polys+=self.group[i].to_polygon(Npts_arc)
            if(type(g)==Ring):
                polys+=self.group[i].to_polygon(Npts_arc)
            if(type(g)==Arc):
                polys+=self.group[i].to_polygon(Npts_arc,split_arc)
                    
                    

        self.group[:] = [g for g in self.group if type(g)==SRef or type(g)==ARef]
        self.group = self.group+polys.group    
    
    def poly_to_circle(self, thresh: float = 0.95, vcount: int = 10, include_refs: bool = True):
        """
        Converts all polygons to circle, when they meet a circularity threshold and
        a vertex count larger than the vcount parameter.
        

        Parameters
        ----------
        thresh : float, optional
            Circularity threshold (1=perfect circle). The default is 0.95.
        vcount : int, optional
            Minimum number of vertices to perform the conversion. The default is 10.
        include_refs : bool, optional
            Perform recursive conversion to SRefs and ARefs. The default is True

        Returns
        -------
        None.

        """
        polys = GeomGroup();
        for i in range(len(self.group)):
            if (type(self.group[i])==Poly):
                convp = self.group[i].to_circle(thresh,vcount)
                if(convp.group==[]):
                    polys.group+=[self.group[i]]
                else:
                    polys+=convp
                continue
            if (type(self.group[i])==SRef or type(self.group[i])==ARef):                
                if(include_refs):
                    self.group[i].group.poly_to_circle(thresh,vcount)
                continue
            # None of the above, just keep
            polys.group+=[self.group[i]]
        
        self.group[:] = [g for g in self.group if type(g)==SRef or type(g)==ARef]
        self.group = self.group+polys.group    
    
    def in_polygons(self, x: float,y:float) -> bool:
        """
        Checks if a given coordinate is inside the GeomGroup polygons. 

        Parameters
        ----------
        x : float
            x coordinate.
        y : float
            y coordinate.

        Returns
        -------
        bool
            True if coorinate is inside the polygon.

        """
        for i in range(len(self.group)):
            if(type(self.group[i])==Poly):
                if(self.group[i].point_inside(x,y)):
                    return True
        return False
    
    def keep_refs_only(self):
        """
        Keeps only the Sref and Aref (can be used to keep a skeleton of the structure)

        Returns
        -------
        Nothing

        """
        self.group[:] =  [g for g in self.group if type(g)==SRef or type(g)==ARef]
        
                   
    
    def __get_boopy__(self,layer: int):
        pg0 = boopy.PolyGroup()
        for i in range(len(self.group)):
            if(type(self.group[i])==Poly and self.group[i].layer==layer):
                pdata = self.group[i].int_data()
                pg0.addPolyData(pdata)
        return pg0
    
    def __set_boopy__(self, pg0,layer: int):
        npoly = pg0.getPolyCount()
        polys = GeomGroup();
        for i in range(npoly):
            poly = Poly([],[],layer)
            pdata = np.array(pg0.getPoly(i))
            pdata =pdata/1000.0
            poly.set_data(pdata)
            polys.add(poly)
        self.group = self.group + polys.group
    
    def boolean_union(self,layer: int):
        """
        Performs a full boolean union (OR) of all polygons in the group matching a layer
        All other elements (circles, paths, texts) are ignored unless they have been already
        converted to polygons

        Parameters
        ----------
        layer : int
            The layer in which the union should be performed.

        Returns
        -------
        Reference to the the object.

        """
        # Get the boost python data
        pg0 = self.__get_boopy__(layer)
        # Remove the old polygons
        self.group[:] = [g for g in self.group if not (type(g)==Poly and g.layer==layer)]
        pg0.assign()
        # Put back the boost python data 
        self.__set_boopy__(pg0, layer)
        return self

    def boolean_difference(self, targetB: "GeomGroup", layerA: int, layerB: int):
        """
        Performs a full difference between the polygons in the calling group matching layerA
        and the polygons in group targetB, matching layerB.
        All other elements (circles, paths, texts) are ignored unless they have been already
        converted to polygons

        Parameters
        ----------
        targetB: GeomGroup
            The geometry to be subtracted.
        layerA : int
            The layer from which subtraction should be performed.
        layerB: int
            The layer to be subtracted.

        Returns
        -------
        Reference to the the object.

        """
        # Get the boost python data
        pgA = self.__get_boopy__(layerA)
        pgB = targetB.__get_boopy__(layerB)
        # Difference
        pgA.difference(pgB)
        # Remove the old polygons
        self.group[:] = [g for g in self.group if not (type(g)==Poly and g.layer==layerA)]
        # Put back the boost python data (merge is automatically done)
        self.__set_boopy__(pgA, layerA)
        return self
        
    def boolean_xor(self, targetB: "GeomGroup", layerA: int, layerB: int):
        """
        Performs an exclusive-OR operation between the polygons in the calling group matching layerA
        and the polygons in group targetB, matching layerB.
        All other elements (circles, paths, texts) are ignored unless they have been already
        converted to polygons

        Parameters
        ----------
        targetB: GeomGroup
            The geometry to be x-OR 'ed.
        layerA : int
            The layer from which XOR operation should be performed.
        layerB: int
            The layer to be XOR 'ed.

        Returns
        -------
        Reference to the the object.

        """
        # Get the boost python data
        pgA = self.__get_boopy__(layerA)
        pgB = targetB.__get_boopy__(layerB)
        # Difference
        pgA.exor(pgB)
        # Remove the old polygons
        self.group[:] = [g for g in self.group if not (type(g)==Poly and g.layer==layerA)]
        # Put back the boost python data (merge is automatically done)
        self.__set_boopy__(pgA, layerA)
        return self
        
    def boolean_intersection(self, targetB: "GeomGroup", layerA: int, layerB: int):
        """
        Performs a full intersection (AND) between the polygons in the calling group matching layerA
        and the polygons in group targetB, matching layerB.
        All other elements (circles, paths, texts) are ignored unless they have been already
        converted to polygons

        Parameters
        ----------
        targetB: GeomGroup
            The geometry to be intersected.
        layerA : int
            The layer from which subtraction should be performed.
        layerB: int
            The layer to be subtracted.

        Returns
        -------
        Reference to the the object.

        """
        # Get the boost python data
        pgA = self.__get_boopy__(layerA)
        pgB = targetB.__get_boopy__(layerB)
        # Difference
        pgA.intersection(pgB)
        # Remove the old polygons
        self.group[:] = [g for g in self.group if not (type(g)==Poly and g.layer==layerA)]
        # Put back the boost python data (merge is automatically done)
        self.__set_boopy__(pgA, layerA)
        return self
        
    def poly_resize(self, offset: float, layer: int, corner_fill_arc: bool = False, num_circle_segments: int = 0):
        """
        Offsets the polygon by a certain distance. Acts only on polygons and on
        a single layer. 

        Parameters
        ----------
        offset : float
            Positive or negative offset (resizing) amount.
        layer : int
            The layer to be resized.
        corner_fill_arc : bool, optional
            Rounds the convex corners. The default is False.
        num_circle_segments : int, optional
            If corner_fill_arc is True, the number of segments to be used for arc filling. The default is 0.

        Returns
        -------
        Reference to the the object.

        """
        pg0 = self.__get_boopy__(layer)
        pg0.resize(round(offset*1000),corner_fill_arc, num_circle_segments)
        self.group[:] = [g for g in self.group if not (type(g)==Poly and g.layer==layer)]
        self.__set_boopy__(pg0, layer)
        return self
        
    def poly_anisotropic_resize(self, angles: list, deltas: list, layer: int):
        """
        Performs an anisotropic offset of the polygons in a given layer.
        Requires an offset array in deltas matching the
        angle of expansion. Angles should cover -90-90

        Parameters
        ----------
        angles : list
            list of angles in degrees.
        deltas : list
            offset at a given angle.
        layer : int
            the layer to be resized.

        Returns
        -------
        Reference to the the object.

        """
        for i in range(len(self.group)):
            if(type(self.group[i])==Poly and self.group[i].layer==layer):
                self.group[i].anisotropic_resize(angles,deltas)
        return self
    
    def poly_outlining(self, offset: float, layer: int, distance: float = 0, corner_fill_arc: bool = False, num_circle_segments: int = 0):
        """
        Calculates the polygon outline by resizing and subtracting the original geometry.
        Also works on circles (ignores the other elements, which must be converted to poly first)

        Parameters
        ----------
        offset : float
            Positive or negative offset (resizing) amount.
        layer : int
            The layer to be resized.
        distance: float, optional
            How far should the outline be displaced from the polygon edge. 
            Negative values mean inward distance. The default is 0.
        corner_fill_arc : bool, optional
            Rounds the convex corners. The default is False.
        num_circle_segments : int, optional
            If corner_fill_arc is True, the number of segments to be used for arc filling. The default is 0.

        Returns
        -------
        Reference to the the object.

        """
        pg0 = self.__get_boopy__(layer)
        pgorig = self.__get_boopy__(layer)
        if(distance != 0):
            pg0.resize(round((offset+distance)*1000),corner_fill_arc, num_circle_segments)
            pgorig.resize(round(distance*1000),corner_fill_arc,num_circle_segments)
        else:
            pg0.resize(round(offset*1000),corner_fill_arc, num_circle_segments)
        self.group[:] = [g for g in self.group if not (type(g)==Poly and g.layer==layer)]
        if(offset>0):
            pg0.difference(pgorig)
            self.__set_boopy__(pg0,layer)
        else:
            pgorig.difference(pg0)
            self.__set_boopy__(pgorig,layer)
            
        #Circles
        for i in range(len(self.group)):
            if type(self.group[i])==Circle:
                g = self.group[i]
                self.group[i] = Arc(g.x0,g.y0,g.r+offset/2+distance,g.r+offset/2+distance,g.layer,0,offset,0,360)            
                
        return self
    
    def invert(self, layer: int, offset: float = 0):      
        """
        Performs the inverse boolean operation (NOT) on a group.
        Acts on the specified layer only. 
        The result is the negative of the mask on the bounding box polygon.
        An offset can be specified to bloat/shrink the bounding box before inversion.

        Parameters
        ----------
        layer : int
            The layer to be inverted.
        offset : float, optional
            Resizing amount (positive or negative) of the bounding box before inversion. The default is 0.

        Returns
        -------
        reference to the inverted object.

        """
        pg0 = self.__get_boopy__(layer)
        sel = self.select_layer(layer)
        if len(sel.group)==0: 
            return self
        bb = sel.bounding_box().toRect();
        bb.set_layer(layer)
        if(offset!=0):
            bb.poly_resize(offset, layer)
        pgm = bb.__get_boopy__(layer)
        pgm.difference(pg0)
        self.group[:] = [g for g in self.group if not (type(g)==Poly and g.layer==layer)]        
        self.__set_boopy__(pgm, layer)
        
        return self
        
       
    def trapezoids(self,layer: int):
        """
        Converts and fractures all polygons in a set of trapezoids.

        Parameters
        ----------
        layer : int
            the layer to be fractured.

        Returns
        -------
        Reference to the the object.

        """
        pg0 = self.__get_boopy__(layer)
        pg0.trapezoids()
        self.group[:] = [g for g in self.group if not (type(g)==Poly and g.layer==layer)]
        self.__set_boopy__(pg0, layer)
        return self
    
    def poly_filter(self, keep_str: str) -> int:
        """
        Performs filtering of vertices based on a condition string.
        Possible conditions are expressed based on the following variables
        'A': "Three-point polygon unsigned area",
        'As': "Three-point polygon signed area",
        'P': "three point perimeter",
        'S': "Shape index of the triangle (4*pi*A/(P**2))",
        'x': "x-coordinate of query point",
        'y': "y-coordinate of query point",
        'xm': "x-coordinate of previous point",
        'ym': "y-coordinate of previous point",
        'xp': "x-coordinate of next point",
        'yp': "y-coordinate of next point",
        'dm': "distance between query point and previous point",
        'dp': "distance between query point and next point",
        'd0': "distance between previous and next point"
        These variables are defined over 3 consecutive points.
        If the condition is met, the middle point is kept, otherwise
        it is discarded and the next 3 points are tested. All layers are used

        Parameters
        ----------
        keep_str : str
            String that contains the condition to keep a vertex or not.

        Raises
        ------
        NameError
            If a name that is not allowed is used.

        Returns
        -------
        int
            The number of vertices discarded.

        """
        ndisc = 0
        for g in self.group:
            if(type(g)==Poly):
                ndisc+=g.three_point_filter(keep_str)
        return ndisc

class Dot:
    def __init__(self,x,y):
        self.x=x
        self.y=y
    
    def translate(self,dx,dy):
        self.x+=dx
        self.y+=dy
        
    def rotate(self,x0,y0,rot):
        xc=self.x-x0
        yc=self.y-y0
        cost = math.cos(rot/180*math.pi)
        sint = math.sin(rot/180*math.pi)
        self.x=cost*xc-sint*yc+x0
        self.y=sint*xc+cost*yc+y0
    
    def rotate_translate(self, x0, y0, rot):
        cost = math.cos(rot/180*math.pi)
        sint = math.sin(rot/180*math.pi)
        x=self.x
        y=self.y
        self.x = (cost*(x)-sint*(y)+x0)
        self.y = (sint*(x)+cost*(y)+y0)
    
    def scale(self,x0,y0,scale_x,scale_y):
        self.x = (self.x-x0)*scale_x+x0
        self.y = (self.y-y0)*scale_y+y0
        
    def mirrorX(self,x0):
        self.x = 2*x0-self.x
        
    def mirrorY(self,y0):
        self.y = 2*y0-self.y
   
class Box:
    def __init__(self,llx: float, lly: float, width: float, height: float):
        '''
        Initialize a box object (not for drawing)

        Parameters
        ----------
        llx : float
            lower-left x-coordinate.
        lly : float
            lower-left y-coordinate.
        width : float
            width of the box.
        height : float
            height of the box.

        Returns
        -------
        None.

        '''
        self.llx = llx
        self.lly = lly
        self.width = width
        self.height = height
    
    def cx(self):
        '''
        The x-coordinate of the box center

        Returns
        -------
        float
            x-coordinate of the box center.

        '''
        return self.llx+self.width/2
    
    def cy(self):
        '''
        The y-coordinate of the box center

        Returns
        -------
        float
            y-coordinate of the box center.

        '''

        return self.lly+self.height/2
    
    def urx(self):
        '''
        The x-coordinate of the upper-right corner

        Returns
        -------
        float
            x-coordinate of the upper-right corner.

        '''

        return self.llx+self.width
    
    def ury(self):
        '''
        The y-coordinate of the upper-right corner

        Returns
        -------
        float
            y-coordinate of the upper-right corner.

        '''

        return self.lly+self.height
    
    def combine(self,other: "Box"):
        '''
        Extends the box to fit another box "other"

        Parameters
        ----------
        other : 'Box'
            The other box that should be combined.

        Returns
        -------
        None.

        '''
        tmp_urx = self.urx()
        tmp_ury = self.ury()
        if other.llx < self.llx:
            self.llx = other.llx
        if other.lly < self.lly:
            self.lly = other.lly
        if other.urx() > tmp_urx:
            tmp_urx=other.urx()
        if other.ury() > tmp_ury:
            tmp_ury = other.ury()
            
        self.width = tmp_urx-self.llx
        self.height = tmp_ury-self.lly
            
    def toPoly(self):
        """
        Creates a Poly object (not for drawing)

        Returns
        -------
        Poly
            The poly representing the box.

        """
        return Poly([self.llx,self.urx(),self.urx(),self.llx],
             [self.lly,self.lly,self.ury(),self.ury()],0)
    
    def toRect(self) ->"GeomGroup":
        """
        Creates a group with a rectangle (as in make_rect), for drawing

        Returns
        -------
        g : GeomGroup
            The group containing the bounding box rectangle.

        """
        g=GeomGroup()
        g.add(self.toPoly())
        return g
    
    def get_numkey_point(self, numkey: int) -> tuple:
        """
        Returns a tuple with x,y coordinate of the point matching the numerical
        keypad (e.g. 5 is the center, 1 is the lower left corner, etc...)
        

        Parameters
        ----------
        numkey : int
            A number between 1 and 9 corresponding to the box point.

        Returns
        -------
        tuple
            The coordinates corresponding to the keypad.

        """
        if(numkey<1 or numkey>9): numkey=5
        xoff = -((numkey-1)%3-1)
        yoff = math.floor((9-numkey)/3)-1
        return (self.cx()-xoff*self.width/2,self.cy()-yoff*self.height/2)
        
    

class Poly:
    def set_points(self,xpts,ypts):
        # Note: only for polygon class, we store the points in GDS format,
        # already scaled to nanometers and as X0,Y0,X1,Y1,X2,Y2...
        # rdata = np.round_((np.array([xpts,ypts])*1000)).astype(int)
        rdata = np.array([xpts,ypts],dtype="float64")
        self.data = np.transpose(rdata).reshape(-1)
        self.data = np.append(self.data,self.data[0:2])
        self.Npts = math.floor(self.data.size/2)
    
    def set_data(self, data):
        self.data = data
        self.Npts = math.floor(self.data.size/2)
        
    def int_data(self):
        return np.round(self.data*1000).astype(int)
    
    def set_int_data(self, idata):
        self.data = idata.astype("float64")/1000;
        self.Npts = self.data.size/2
    
    def __init__(self,xpts,ypts,layer):
        self.layer = layer
        self.set_points(xpts,ypts)
        
    def translate(self,dx,dy):
        self.data[0::2]+=dx
        self.data[1::2]+=dy        
    
    def rotate_translate(self,x0,y0,rot):
        cost = math.cos(rot/180*math.pi)
        sint = math.sin(rot/180*math.pi)
        x = np.copy(self.data[0::2])
        y = np.copy(self.data[1::2])
        self.data[0::2] = (cost*(x)-sint*(y)+x0)
        self.data[1::2] = (sint*(x)+cost*(y)+y0)
        
    def rotate(self,x0,y0,rot):
        cost = math.cos(rot/180*math.pi)
        sint = math.sin(rot/180*math.pi)
        x = np.copy(self.data[0::2])
        y = np.copy(self.data[1::2])
        self.data[0::2] = cost*(x-x0)-sint*(y-y0)+x0
        self.data[1::2] = sint*(x-x0)+cost*(y-y0)+y0
    
    def scale(self,x0,y0,scale_x,scale_y):
        x = self.data[0::2]
        y = self.data[1::2]
        self.data[0::2] = scale_x*(x-x0)+x0
        self.data[1::2] = scale_y*(y-y0)+y0
            
    def mirrorX(self,x0):
        self.data[0::2] = 2*x0-self.data[0::2]

    def mirrorY(self,y0):
        self.data[1::2] = 2*y0-self.data[1::2]
        
    def bounding_box(self):
        llx = min(self.data[0::2])
        urx = max(self.data[0::2])
        lly = min(self.data[1::2])
        ury = max(self.data[1::2])
        return Box(llx,lly,urx-llx,ury-lly)
    
    def area(self):
        area = 0.0;
        x = self.data[0::2]
        y = self.data[1::2]
        n = int(len(x))
        j = n-1
        for i in range(n):
            area += x[j]*y[i] - x[i]*y[j]
            j=i
        return float(round(1e6*abs(area / 2.0)))/1.0e6
    
    def centroid(self):
        cx=0;
        cy=0;
        area=0;        
        x = self.data[0::2]
        y = self.data[1::2]
        n = int(len(x))
        j = n-1
        for i in range(n):
            shl = x[j]*y[i] - x[i]*y[j]
            area +=  shl
            cx+=(x[j]+x[i])*shl
            cy+=(y[j]+y[i])*shl
            j=i
        cx/=3*area
        cy/=3*area
        return cx,cy
    
    def perimeter(self):
        p = 0;
        x = self.data[0::2]
        y = self.data[1::2]
        n = int(len(x))
        j = n-1
        for i in range(n):
            p+=np.sqrt((x[i]-x[j])**2+(y[i]-y[j])**2)
            j=i
        return p
    
    def three_point_filter(self,keep_str: str) -> int:
        """
        Performs filtering of vertices based on a condition string.
        Possible conditions are expressed based on the following variables
        'A': "Three-point polygon unsigned area",
        'As': "Three-point polygon signed area",
        'P': "three point perimeter",
        'S': "Shape index of the triangle (4*pi*A/(P**2))",
        'x': "x-coordinate of query point",
        'y': "y-coordinate of query point",
        'xm': "x-coordinate of previous point",
        'ym': "y-coordinate of previous point",
        'xp': "x-coordinate of next point",
        'yp': "y-coordinate of next point",
        'dm': "distance between query point and previous point",
        'dp': "distance between query point and next point",
        'd0': "distance between previous and next point"
        These variables are defined over 3 consecutive points.
        If the condition is met, the middle point is kept, otherwise
        it is discarded and the next 3 points are tested.

        Parameters
        ----------
        keep_str : str
            String that contains the condition to keep a vertex or not.

        Raises
        ------
        NameError
            If a name that is not allowed is used.

        Returns
        -------
        int
            The number of vertices discarded.

        """
        allowed_names = {'A': "Three-point polygon unsigned area",
                         'As': "Three-point polygon signed area",
                         'P': "three point perimeter",
                         'S': "Shape index of the triangle (4*pi*A/(P**2))",
                         'x': "x-coordinate of query point",
                         'y': "y-coordinate of query point",
                         'xm': "x-coordinate of previous point",
                         'ym': "y-coordinate of previous point",
                         'xp': "x-coordinate of next point",
                         'yp': "y-coordinate of next point",
                         'dm': "distance between query point and previous point",
                         'dp': "distance between query point and next point",
                         'd0': "distance between previous and next point"}
        code = compile(keep_str,"<string>","eval")
        for name in code.co_names:
            if(name not in allowed_names):
                raise NameError(f"Use of expression {name} not allowed")
        
#        g.group[:] = [sflat.group[i] for i,val in enumerate(sel) if val]
 #       return g
        x = self.data[0::2]
        y = self.data[1::2]
        xf = []
        yf = []
        n = int(self.Npts)
        ndisc = 0
        j = n-1
        k = n-2
        for i in range(n):
            Atri = x[i]*(y[j]-y[k])+x[j]*(y[k]-y[i]) + x[k]*(y[i]-y[j])
            d1 = np.sqrt((x[i]-x[j])**2+(y[i]-y[j])**2)
            d2 = np.sqrt((x[j]-x[k])**2+(y[j]-y[k])**2)
            d3 = np.sqrt((x[i]-x[k])**2+(y[i]-y[k])**2)
            allowed_names["A"]=abs(Atri)/2
            allowed_names["As"]=Atri/2
            allowed_names["P"]=d1+d2+d3
            allowed_names["S"]=abs(Atri)*2*np.pi/allowed_names["P"]**2
            allowed_names["x"]=x[j]
            allowed_names["y"]=y[j]
            allowed_names["xm"]=x[k]
            allowed_names["ym"]=y[k]
            allowed_names["xp"]=x[i]
            allowed_names["yp"]=y[i]
            allowed_names["dm"]=d2
            allowed_names["dp"]=d1
            allowed_names["d0"]=d3            
            sel = eval(code, {"__builtins__": {}}, allowed_names)
            if(sel):
                xf+=[x[j]]
                yf+=[y[j]]
                k=j
                j=i
            else:
                ndisc+=1
                j=i
        self.set_points(xf,yf)
        return ndisc
        
            
    
    def to_polygon(self):
        g = GeomGroup()
        g.add(self)
        return g

    def to_circle(self, thresh: float = 0.95, vcount: int = 10):
        g = GeomGroup()
        if(self.Npts<vcount): 
            return g
        # Attempt to perform a conversion, return empty group if failed
        # Check circularity
        xpts = self.data[0::2]
        ypts = self.data[1::2]
        cx,cy = self.centroid()
        rpts = np.sqrt((xpts-cx)**2+(ypts-cy)**2)
        r_avg = rpts.mean()
        rmin = np.min(rpts)
        rmax = np.max(rpts)
        circularity = 1-(rmax-rmin)/r_avg;
        if(circularity>=thresh):
            g.add(Circle(cx,cy,r_avg,self.layer))
        return g
        
    def identical_to(self, p2: "Poly"):
        x = self.data[0::2]
        y = self.data[1::2]
        x2 = p2.data[0::2]
        y2 = p2.data[1::2]
        x3 = np.append(x,x)
        y3 = np.append(y,y)
        for e in range(0, len(x)):
            k = 0
            for w in range(e, e + len(x)):
                if x2[k]==x3[w] and y2[k]==y3[w]:
                    k+= 1
                else:
                    break
            # if all n elements are same circularly
            if k == len(x):
                return True
        return False

    def point_inside(self,x,y):
        c = False
        n = self.Npts
        xpts = self.data[0::2]
        ypts = self.data[1::2]
        bpx = xpts[0]
        bpy = ypts[0]
        for i in range(n-1):
            fpx = xpts[i+1]
            fpy = ypts[i+1]
            a = (fpy > y) != (bpy > y)
            #print(a)
            if(bpy-fpy==0):
                b=True
            else:
                b = x < ((bpx - fpx)*(y-fpy)/(bpy-fpy)+fpx)
            #print(b)
            if(  a and b ): c= not c
            bpx = fpx
            bpy = fpy
        return c
    
    def anisotropic_resize(self,angle,deltas):
        """
        Performs an anisotropic offset of the polygon 
        Requires an offset array in deltas matching the
        angle of expansion. Angles should cover -90-90

        Parameters
        ----------
        angle : list
            list of angles in degrees.
        deltas : list
            offset at a given angle.

        Returns
        -------
        None.

        """
        xpts = self.data[0::2]
        ypts = self.data[1::2]
        normals = []
        for i in range(len(xpts)-1):
            x1 = xpts[i]
            y1 = ypts[i]
            x2 = xpts[i+1]
            y2 = ypts[i+1]
            # calculate normal
            b = x1-x2
            a = y2-y1
            c = x2*y1-x1*y2
            
            nf = math.sqrt(a*a+b*b)
            nx = b/nf
            ny = a/nf
            alpha = math.degrees(math.atan2(ny,nx))
            
            d = np.interp(alpha,angle,deltas)
            c+=nf*d;
            normals.append([a,b,c])
    
        xpts = []
        ypts = []
        normals.append(normals[0])
        for i in range(len(normals)-1):
            n1 = normals[i]
            n2 = normals[i+1]
            D = n2[1]*n1[0]-n2[0]*n1[1]
            x = -n1[2]*n2[1]+n2[2]*n1[1]
            y = +n1[2]*n2[0]-n2[2]*n1[0]
            xpts.append(x/D)
            ypts.append(y/D)
        self.set_points(xpts, ypts)
        

class Path:
    def __init__(self,xpts,ypts,width,layer):
        self.xpts = xpts
        self.ypts = ypts
        self.width = width
        self.layer = layer
        self.Npts = len(xpts)
    
    def translate(self,dx,dy):
        for i in range(self.Npts):
            self.xpts[i]=self.xpts[i]+dx
            self.ypts[i]=self.ypts[i]+dy
            
    def rotate_translate(self,x0,y0,rot):
        cost = math.cos(rot/180*math.pi)
        sint = math.sin(rot/180*math.pi)
        for i in range(self.Npts):
            x=self.xpts[i]
            y=self.ypts[i]
            self.xpts[i]=cost*(x)-sint*(y)+x0
            self.ypts[i]=sint*(x)+cost*(y)+y0
       
    def rotate(self,x0,y0,rot):
        cost = math.cos(rot/180*math.pi)
        sint = math.sin(rot/180*math.pi)
        for i in range(self.Npts):
            x=self.xpts[i]
            y=self.ypts[i]
            self.xpts[i]=cost*(x-x0)-sint*(y-y0)+x0
            self.ypts[i]=sint*(x-x0)+cost*(y-y0)+y0
    
    def scale(self,x0,y0,scale_x,scale_y):
        for i in range(self.Npts):
            x=self.xpts[i]
            y=self.ypts[i]
            self.xpts[i]=scale_x*(x-x0)+x0
            self.ypts[i]=scale_y*(y-y0)+y0
            self.width*=scale_x
            
    def mirrorX(self,x0):
        for i in range(self.Npts):
            self.xpts[i]=2*x0-self.xpts[i]

    def mirrorY(self,y0):
        for i in range(self.Npts):
            self.ypts[i]=2*y0-self.ypts[i]
            
    def bounding_box(self):
        llx = min(self.xpts)
        urx = max(self.xpts)
        lly = min(self.ypts)
        ury = max(self.ypts)
        return Box(llx,lly,urx-llx,ury-lly)

    def path_length(self):
        x=self.xpts
        y=self.ypts
        plen = 0.0
        for i in range(1,self.Npts):
            plen+=np.sqrt((x[i]-x[i-1])**2 + (y[i]-y[i-1])**2)
        return plen
        
    def area(self):
        # Approximately the path length * width
        return self.path_length()*self.width
    
    def centroid(self):
        # Give the average x,y
        cx = np.array(self.xpts).mean()
        cy = np.array(self.ypts).mean()
        return cx,cy
    
    def perimeter(self):
        # Approximately twice the length and twice width
        return self.path_length()*2+self.width*2
        
    def to_polygon(self):
        x=self.xpts
        y=self.ypts
        w=self.width
        p1 = Poly([0],[0],self.layer)
        if(self.Npts==1):
            p1.set_points([-w/2,w/2,w/2,-w/2],[-w/2,-w/2,w/2,w/2])
            p1.translate(x,y)
            
        if(self.Npts==2):
            ang1 = math.atan2(y[1]-y[0],x[1]-x[0]);
            c1 = w/2*math.cos(ang1-math.pi/2);
            c2 = w/2*math.cos(ang1+math.pi/2);
            s1 = w/2*math.sin(ang1-math.pi/2);
            s2 = w/2*math.sin(ang1+math.pi/2);
            p1.set_points([x[0]+c1,x[1]+c1,x[1]+c2,x[0]+c2],
                          [y[0]+s1,y[1]+s1,y[1]+s2,y[0]+s2])

        if(self.Npts>2):
            xp1 = []
            yp1 = []
            xp2 = []
            yp2 = []
            for j in range(1,self.Npts-1):
                ang1 = math.atan2(y[j]-y[j-1],x[j]-x[j-1])
                ang2 = math.atan2(y[j+1]-y[j],x[j+1]-x[j])
                d = (x[j+1]-x[j-1])*(y[j]-y[j-1])\
                    - (y[j+1]-y[j-1])*(x[j]-x[j-1])
                if(j==1):
                    xp1.append(x[j-1]+w/2*math.cos(ang1-math.pi/2));
                    yp1.append(y[j-1]+w/2*math.sin(ang1-math.pi/2));
                    xp2.append(x[j-1]+w/2*math.cos(ang1+math.pi/2));
                    yp2.append(y[j-1]+w/2*math.sin(ang1+math.pi/2));
                    
                if(d<0):
                    xp1.append(x[j]+w/2*math.cos(ang1-math.pi/2));
                    yp1.append(y[j]+w/2*math.sin(ang1-math.pi/2));
                    xp1.append(x[j]+w/2*math.cos(ang2-math.pi/2));
                    yp1.append(y[j]+w/2*math.sin(ang2-math.pi/2));
                    wx = w/2/math.cos((ang2-ang1)/2);
                    a0 = math.pi/2-(ang1+ang2)/2;
                    xp2.append(x[j]-wx*math.cos(a0));
                    yp2.append(y[j]+wx*math.sin(a0));
                else:
                    xp2.append(x[j]+w/2*math.cos(ang1+math.pi/2));
                    yp2.append(y[j]+w/2*math.sin(ang1+math.pi/2));
                    xp2.append(x[j]+w/2*math.cos(ang2+math.pi/2));
                    yp2.append(y[j]+w/2*math.sin(ang2+math.pi/2));
                    wx = w/2/math.cos((ang2-ang1)/2);
                    a0 = math.pi/2-(ang1+ang2)/2;
                    xp1.append(x[j]+wx*math.cos(a0));
                    yp1.append(y[j]-wx*math.sin(a0));
                if(j==self.Npts-2):
                    xp1.append(x[j+1]+w/2*math.cos(ang2-math.pi/2));
                    yp1.append(y[j+1]+w/2*math.sin(ang2-math.pi/2));
                    xp2.append(x[j+1]+w/2*math.cos(ang2+math.pi/2));
                    yp2.append(y[j+1]+w/2*math.sin(ang2+math.pi/2));
            
            xp2.reverse()
            yp2.reverse()
            p1.set_points(xp1+xp2,yp1+yp2)
        g = GeomGroup();
        g.add(p1)
        return g


class Text:
    def __init__(self,x0,y0,text,posu,posv,height,width,angle,layer):
        self.x0=x0
        self.y0=y0
        self.text=text
        self.posu=posu
        self.posv=posv
        self.height=height
        self.width=width
        self.angle=angle
        self.layer=layer
        
    def translate(self,dx,dy):
        self.x0+=dx
        self.y0+=dy
    
    def rotate_translate(self, dx,dy,rot):
        cost = math.cos(rot/180*math.pi)
        sint = math.sin(rot/180*math.pi)
        xv = self.x0;
        yv = self.y0;
        self.x0 = cost*xv-sint*yv+dx
        self.y0 = sint*xv+cost*yv+dy
        self.angle += rot
    
    def rotate(self,xc,yc,rot):
        cost = math.cos(rot/180*math.pi)
        sint = math.sin(rot/180*math.pi)
        xv = self.x0-xc;
        yv = self.y0-yc;
        self.x0 = cost*xv-sint*yv+xc
        self.y0 = sint*xv+cost*yv+yc
        self.angle += rot
        
    def scale(self,xc,yc,scale_x,scale_y):
        self.x0 = scale_x*(self.x0-xc)+xc
        self.y0 = scale_y*(self.y0-yc)+yc
        self.height *= scale_y
        self.width *=scale_x
        
    def mirrorX(self,xc):
        self.x0 = 2*xc-self.x0
        self.angle=180-self.angle

    def mirrorY(self,yc):
        self.y0 = 2*yc-self.y0
        self.angle=-self.angle
        
    def bounding_box(self):
        # Note this cannot be properly estimated
        return Box(self.x0,self.y0,0,0)

    def area(self):
        return 0
    
    def centroid(self):
        return self.x0,self.y0
    
    def perimeter(self):
        return 0
    
    def __to_path(self):
        offset =0;
        g = GeomGroup();
        for c in self.text:
            #print("processing letter %s" % c)
            if(c==' '):
                offset+=self.height
            if c in _glyphs:
                letter = deepcopy(_glyphs[c][0])
                letter.set_layer(self.layer)
                letter.scale(0, 0, self.height,self.height)
                for p in letter.group:
                    # Note there are only paths in the group
                    p.width=self.width 
                letter.translate(offset, 0)
                g+=letter
                offset += _glyphs[c][1]*self.height
        # Now shift depending on posu/posv
        # offset contains the length of the text
        g.translate(-self.posu*offset/2,(self.posv-2)*self.height/2)
        g.rotate(0,0,self.angle)
        g.translate(self.x0, self.y0)
        return g
        
    def to_polygon(self):
        g = self.__to_path()
        g.path_to_poly()
        return g

class RefBase:
    def __init__(self,x0,y0,mag,angle,mirror):
        self.x0=x0
        self.y0=y0
        self.mag=mag
        self.angle=angle
        self.mirror=mirror
        self.layer = 0 # Unused
    
    def translate(self,dx,dy):
        self.x0+=dx
        self.y0+=dy
        
    def rotate_translate(self,dx,dy,rot):
        cost = math.cos(rot/180*math.pi)
        sint = math.sin(rot/180*math.pi)
        xv = self.x0;
        yv = self.y0;
        self.x0 = cost*xv-sint*yv+dx
        self.y0 = sint*xv+cost*yv+dy
        self.angle += rot
        self.angle = self.angle%360
        
    def rotate(self,xc,yc,rot):
        cost = math.cos(rot/180*math.pi)
        sint = math.sin(rot/180*math.pi)
        xv = self.x0-xc;
        yv = self.y0-yc;
        self.x0 = cost*xv-sint*yv+xc
        self.y0 = sint*xv+cost*yv+yc
        self.angle += rot
        self.angle = self.angle%360
        
    def scale(self,xc,yc,scale_x,scale_y):
        self.x0 = scale_x*(self.x0-xc)+xc
        self.y0 = scale_y*(self.y0-yc)+yc
        self.mag *= scale_x
        
    def mirrorX(self,xc):
        self.x0 = 2*xc-self.x0
        self.mirror=not self.mirror
        self.angle=180-self.angle
        self.angle = self.angle%360

    def mirrorY(self,yc):
        self.y0 = 2*yc-self.y0
        self.mirror = not self.mirror
        self.angle = -self.angle
        
    def centroid(self):
        return self.x0,self.y0
                
class SRef(RefBase):
    def __init__(self,x0,y0,cellname,group,mag,angle,mirror):
        RefBase.__init__(self,x0,y0,mag,angle,mirror)
        self.cellname = cellname
        self.group = group
    
    def bounding_box(self):
        if(self.cellname in _BoundingBoxPool):
            bb = _BoundingBoxPool[self.cellname]
        else:
            bb = self.group.bounding_box()
        p = bb.toPoly()
        p.scale(0,0,self.mag,self.mag)
        p.rotate_translate(self.x0,self.y0,self.angle)
        if(self.mirror): 
            p.mirrorY(self.y0)
        return p.bounding_box()
    
    
    def place_group(self,flat_group):
        # scale first
        if(self.mag != 1):
            flat_group.scale(0,0,self.mag,self.mag)
        # roto-translate
        if(self.mirror):
            flat_group.mirrorY(0)
        if(self.angle != 0):
            flat_group.rotate_translate(self.x0,self.y0,self.angle)
        else:
            flat_group.translate(self.x0,self.y0)
        return flat_group

class ARef(SRef):
    def __init__(self,x0,y0,cellname,group,
                 ncols,nrows,ax,ay,bx,by,
                 mag,angle,mirror):
        SRef.__init__(self,x0,y0,cellname,group,mag,angle,mirror)
        self.ncols = ncols
        self.nrows = nrows
        self.ax = ax
        self.ay = ay
        self.bx = bx
        self.by = by

    def bounding_box(self):
        bb=SRef.bounding_box(self);
        bbn = deepcopy(bb)
        for i in range(self.ncols):
            for j in range(self.nrows):
                dx = i*self.ax+j*self.bx
                dy = i*self.ay+j*self.by
                bbn.combine(Box(bb.llx+dx,bb.lly+dy,bb.width,bb.height))
        return bbn

    def place_group(self,flat_group):
        SRef.place_group(self, flat_group)
        base_group = flat_group.copy()
        for i in range(self.ncols):
            for j in range(self.nrows):
                if(i==0 and j==0): continue
                dx = i*self.ax+j*self.bx
                dy = i*self.ay+j*self.by
                ng = base_group.copy()
                ng.translate(dx,dy)
                flat_group+=ng
        return flat_group

class Circle:
    def __init__(self,x0,y0,r,layer):
        self.x0=x0
        self.y0=y0
        self.r=r
        self.layer=layer
        
    def translate(self,dx,dy):
        self.x0+=dx
        self.y0+=dy

    def rotate_translate(self,xc,yc,rot):
        cost = math.cos(rot/180*math.pi)
        sint = math.sin(rot/180*math.pi)
        x = self.x0
        y = self.y0
        self.x0 = cost*x-sint*y+xc
        self.y0 = sint*x+cost*y+yc
    
    def rotate(self,xc,yc,rot):
        cost = math.cos(rot/180*math.pi)
        sint = math.sin(rot/180*math.pi)
        x = self.x0
        y = self.y0
        self.x0 = cost*(x-xc)-sint*(y-yc)+xc
        self.y0 = sint*(x-xc)+cost*(y-yc)+yc
        
    def scale(self,xc,yc,scale_x,scale_y):
        self.x0 = scale_x*(self.x0-xc)+xc
        self.y0 = scale_y*(self.y0-yc)+yc
        self.r = scale_x*self.r
        
    def mirrorX(self,xc):
        self.x0 = 2*xc-self.x0

    def mirrorY(self,yc):
        self.y0 = 2*yc-self.y0
        
    def bounding_box(self):
        return Box(self.x0-self.r,self.y0-self.r,2*self.r,2*self.r)
    
    def area(self):
        return np.pi*self.r*self.r
    
    def centroid(self):
        return self.x0, self.y0
    
    def perimeter(self):
        return 2*np.pi*self.r
    
    def to_polygon(self,Npts=12):
        xc = np.array([0.]*Npts)
        yc = np.array([0.]*Npts)
        for i in range(Npts):
            xc[i]=math.cos(i*2*math.pi/Npts)
            yc[i]=math.sin(i*2*math.pi/Npts)
        g = GeomGroup()
        g.add(Poly(self.r*xc+self.x0,self.r*yc+self.y0,self.layer))
        return g
        
class Ellipse(Circle):
    def __init__(self,x0,y0,rX,rY,layer,rot):
        Circle.__init__(self,x0,y0,rX,layer)
        self.r1 = rY
        self.rot=rot
    
    def rotate_translate(self, xc,yc,rot):
        Circle.rotate_translate(self, xc, yc, rot)
        self.rot+=rot
        
    def rotate(self,xc,yc,rot):
        Circle.rotate(self,xc,yc,rot)
        self.rot+=rot
    
    def scale(self,xc,yc,scale_x,scale_y):
        Circle.scale(self,xc,yc,scale_x,scale_y)
        self.r1*=scale_y
        
    def mirrorX(self, xc):
        Circle.mirrorX(self,xc)
        self.rot=180-self.rot
    
    def mirrorY(self, yc):
        Circle.mirrorY(self,yc)
        self.rot=-self.rot
    
    def bounding_box(self):
        g = self.to_polygon(12)
        return g.bounding_box()
    
    def area(self):
        return np.pi*self.r*self.r1
    
    def perimeter(self):
        a = self.r
        b = self.r1
        return np.pi*(3*(a+b)-np.sqrt((3*a+b)*(a+3*b)))
    
    def to_polygon(self,Npts=32):
        xc = np.array([0.]*Npts)
        yc = np.array([0.]*Npts)
        for i in range(Npts):
            xc[i]=math.cos(i*2*math.pi/Npts)
            yc[i]=math.sin(i*2*math.pi/Npts)
        g = GeomGroup()
        g.add(Poly(self.r*xc+self.x0,self.r1*yc+self.y0,self.layer))
        g.rotate(self.x0, self.y0, self.rot)
        return g

class Ring(Ellipse):
    def __init__(self,x0,y0,rX,rY,layer,rot,w):
        Ellipse.__init__(self,x0,y0,rX,rY,layer,rot)
        self.w=w
        
    def scale(self,xc,yc,scale_x,scale_y):
        Ellipse.scale(self,xc,yc,scale_x,scale_y)
        self.w*=scale_x
    
    def bounding_box(self):
        g = self.to_polygon(12)
        return g.bounding_box()
    
    def area(self):
        a1 = np.pi*(self.r+self.w/2)*(self.r1+self.w/2)
        a2 = np.pi*(self.r-self.w/2)*(self.r1-self.w/2)
        return a1-a2
    
    def perimeter(self):
        g = self.to_polygon(12)
        return g.group[0].perimeter()
        
    def to_polygon(self,Npts=32):
        xpts = np.array([0.]*(2+Npts*2))
        ypts = np.array([0.]*(2+Npts*2))
        for i in range(1+Npts):
            xpts[i]=math.cos(i*2*math.pi/Npts)*(self.r+self.w/2)+self.x0
            ypts[i]=math.sin(i*2*math.pi/Npts)*(self.r1+self.w/2)+self.y0
        for i in range(1+Npts):
            j = Npts-i;
            xpts[i+1+Npts]=math.cos(j*2*math.pi/Npts)*(self.r-self.w/2)+self.x0
            ypts[i+1+Npts]=math.sin(j*2*math.pi/Npts)*(self.r1-self.w/2)+self.y0
        p1 = Poly(xpts,ypts,self.layer)
        p1.rotate(self.x0,self.y0,self.rot)
        g = GeomGroup()
        g.add(p1)
        return g

class Arc(Ring):
    def __init__(self,x0,y0,rX,rY,layer,rot,w,a1,a2):
        Ring.__init__(self,x0,y0,rX,rY,layer,rot,w)
        self.a1=a1
        self.a2=a2
        
    def bounding_box(self):
        g = self.to_polygon(12)
        return g.bounding_box()
    
    def area(self):
        ra=Ring.area(self)
        return ra * (math.radians(self.a2)-math.radians(self.a1))/2/np.pi
    
    def centroid(self):
        g = self.to_polygon(12)
        return g.group[0].centroid()
    
    def to_polygon(self,Npts=32,autosplit=False):
        Npts+=1
        th = np.linspace(math.radians(self.a1),math.radians(self.a2),Npts)
        xpts1 = np.cos(th)*(self.r+self.w/2)+self.x0
        ypts1 = np.sin(th)*(self.r1+self.w/2)+self.y0
        xpts2 = np.cos(th)*(self.r-self.w/2)+self.x0
        ypts2 = np.sin(th)*(self.r1-self.w/2)+self.y0
        g = GeomGroup()
        if(autosplit):
            for i in range(Npts-1):
                p1 = Poly(np.append(xpts1[i:(i+2)],xpts2[(-Npts+1+i):(-Npts-1+i):-1]),
                          np.append(ypts1[i:(i+2)],ypts2[(-Npts+1+i):(-Npts-1+i):-1]),self.layer)
                p1.rotate(self.x0,self.y0,self.rot)
                g.add(p1)
        else:    
            p1 = Poly(np.append(xpts1,xpts2[::-1]),np.append(ypts1,ypts2[::-1]),self.layer)
            p1.rotate(self.x0,self.y0,self.rot)
            g.add(p1)
        return g


# Load fonts and store the glyphs
# Maybe we should place this somewhere else
caps=dict()
with open(_STENCIL_FONT_PATH, encoding=_STENCIL_FONT_ENCODING) as f: 
    c = 'a';
    for line in f: 
        test = line.rstrip('\n').split(' ')
        if(len(test)==1):
            c = test[0]
            caps[c]=[]
        else:
            nums = list(map(float,test))
            caps[c]+=nums

for i in caps:
    data = caps[i]
    gl = GeomGroup()
    xpts = []
    ypts = []
    for j in range(0,len(data),3):
        x=data[j]/3.6
        y=(data[j+1])/3.6
        flag= data[j+2]
        #print(i,x,y,flag)
        if(flag==0):
            if(j>0):
                gl.add(Path(xpts,ypts,1,0))
            xpts = [x]
            ypts = [y]
        elif(flag>0):
            # append
            xpts.append(x)
            ypts.append(y)
        else:
            gl.add(Path(xpts,ypts,1,0))
    _glyphs[i]=(gl,x)
    
del caps
