"""
Functions that generate shapes into `samplemaker.shapes.GeomGroup` objects.

The concept of "makers"
---------------------
The `samplemaker.makers` module contains functions that are directly related
to the shape objects defined in the `samplemaker.shapes` submodule. 
For each shape, a make_* function is provided. 

Each make_ function returns a `GeomGroup` object, which can be combined with other
objects created by other calls to make_ functions.
Often, the maker function also provides an option to convert the shape to polygon
directly. 

"""

import math
import samplemaker.shapes as smsh
from samplemaker.shapes import GeomGroup

def make_dot(x0: float, y0: float)-> "smsh.Dot":
    """
    Creates a dot object. Dots cannot be exported to GDS but they are useful
    to store coordinates and perform rotations.

    Parameters
    ----------
    x0 : float
        x coordinate in um.
    y0 : float
        y coordinate in um.

    Returns
    -------
    dot : samplemaker.shapes.Dot
        A Dot object.

    """
    return smsh.Dot(x0,y0)
    

def make_poly(xpts: list[float],ypts: list[float],
              layer: int = 1)-> 'GeomGroup':
    """
    Creates a closed polygon object. 
    The first and last point should not be specified twice.

    Parameters
    ----------
    xpts : list[float]
        x coordinates in um.
    ypts : list[float]
        y coordinates in um.
    layer : int, optional
        layer. The default is 1.

    Returns
    -------
    g : GeomGroup
        A group containing a single polygon.

    """
    g = GeomGroup()
    g.add(smsh.Poly(xpts,ypts,layer))
    return g        

def make_path(xpts: list[float],ypts: list[float],
              width: float,layer: int = 1,
              to_poly: bool = 0)-> 'GeomGroup':
    """
    Creates a path object (open line with width).
    Ideally the width should be >0, a width of zero should be avoided.    

    Parameters
    ----------
    xpts : list[float]
        x coordinates in um.
    ypts : list[float]
        y coordinates in um.
    width : float
        path width in um.
    layer : int, optional
        The path layer. The default is 1.
    to_poly : bool, optional
        If true, the path is converted to a polygon. The default is 0.

    Returns
    -------
    g : GeomGroup
        A group containing a single path.

    """
    g = GeomGroup()
    path = smsh.Path(xpts,ypts,width,layer)
    if(to_poly):
        g=path.to_polygon()
    else:
        g.add(path)
    return g

def make_text(x0: float,y0: float,text: str,
              height: float,width: float, numkey: int = 5, angle: float = 0, 
              layer: int = 1, to_poly: bool = 0) -> "GeomGroup":
    """
    Create a text object

    Parameters
    ----------
    x0 : float
        Reference point, x coordinate in um.
    y0 : float
        Reference point, y coordinate in um.
    text : str
        A string containing a text to display.
    height : float
        Text height (note, this is what GDS calls "text width").
    width : float
        The width of the lines composing the text 
        (a good value is 1/10th of height).
    numkey : int, optional
        The numkey specifies the location of the origin (x0,y0) compared to 
        the text position. The reference point x0,y0 can be any of the corners 
        or mid-points specified by the numerical keypad on a standard keyboard. 
        For example numkey=1 means that x0,y0 will be the lower-left corner of 
        the rectangle as 1 is located in the lower-left corner of the numerical
        keypad. Similarly, numkey=9 will be the upper-right corner.
        The default is 5 (=center).
    angle : float, optional
        Text rotation (only used for conversion to polygon). The default is 0.
    layer : int, optional
        The text layer. The default is 1.
    to_poly : bool, optional
        If true, the text is converted to a polygon. The default is 0.

    Returns
    -------
    g : GeomGroup
        A geometry containing a single text element.

    """
    g = GeomGroup();
    if(numkey<1 | numkey>9): numkey = 5
    posu = (numkey-1)%3
    posv = math.floor((9-numkey)/3)
    txt=smsh.Text(x0,y0,text,posu,posv,height,width,angle,layer)
    if(to_poly==1):
        g = txt.to_polygon()
    else:
        g.add(txt)
    return g

def make_sref(x0: float, y0: float, cellname: str, group: "GeomGroup",
              mag: float = 1.0, angle: float = 0, mirror: bool = 0) -> "GeomGroup":
    """
    Create a CELL reference or SREF element in GDS

    Parameters
    ----------
    x0 : float
        X coordinate of CELL position in um.
    y0 : float
        Y coordinate of CELL position in um.
    cellname : str
        A string conaining a valid GDS cell reference name.
    group : "GeomGroup"
        The group of geometries that are being referenced.
    mag : float, optional
        Magnification factor. The default is 1.0.
    angle : float, optional
        Rotation angle of the cell in degrees. The default is 0.
    mirror : bool, optional
        If true, the cell is mirrored along X. The default is 0.

    Returns
    -------
    g : GeomGroup
        A geometry containing a single cell reference.

    """
    g = GeomGroup();
    g.add(smsh.SRef(x0,y0,cellname,group,mag,angle,mirror))
    return g

def make_aref(x0: float, y0: float, cellname: str, group: "GeomGroup",
              ncols: int, nrows: int, ax: float, ay: float, bx: float, by: float,
              mag: float = 1.0, angle: float = 0, mirror: bool = 0) -> "GeomGroup":
    """
    Create an ARRAY of cell references or AREF element in GDS

    Parameters
    ----------
    x0 : float
        X coordinate of CELL position in um.
    y0 : float
        Y coordinate of CELL position in um.
    cellname : str
        A string conaining a valid GDS cell reference name.
    group : "GeomGroup"
        The group of geometries that are being referenced.
    ncols : int
        Number of repetitions along the "a" vector.
    nrows : int
        Number of repetitions along the "b" vector.
    ax : float
        x-component of the "a" base vector.
    ay : float
        y-component of the "a" base vector.
    bx : float
        x-component of the "b" base vector.
    by : float
        y-component of the "b" base vector.
    mag : float, optional
        Magnification factor. The default is 1.0.
    angle : float, optional
        Rotation angle of the cell in degrees. The default is 0.
    mirror : bool, optional
        If true, the cell is mirrored along X. The default is 0.

    Returns
    -------
    g : GeomGroup
        A geometry containing a single array reference to a cell.

    """
    g = GeomGroup();
    g.add(smsh.ARef(x0, y0, cellname, group, ncols, nrows, ax, ay, bx, by, mag, angle, mirror))
    return g

def make_circle(x0: float,y0: float,r: float,layer: int = 1, 
                to_poly: bool = False, vertices: int = 32) -> 'GeomGroup':
    """
    Create a filled circle

    Parameters
    ----------
    x0 : float
        x coordinate of the center in um.
    y0 : float
        y coordinate of the center in um.
    r : float
        radius in um.
    layer : int, optional
        The circle layer. The default is 1.
    to_poly : bool, optional
        If true, the circle is converted to a polygon. The default is 0.
    vertices : int, optional
        Specify the number of vertices to be used for conversion to polygon.
        The default is 32.

    Returns
    -------
    g : GeomGroup
        A geometry containing a single circle.

    """
    g = GeomGroup()
    c = smsh.Circle(x0,y0,r,layer)
    if (to_poly):
        g = c.to_polygon(vertices)
    else:
        g.add(c)
    return g
    
def make_ellipse(x0: float,y0: float,rX: float,rY: float, 
                 rot: float, layer: int = 1,
                 to_poly: bool = 0, vertices: int = 32) -> 'GeomGroup':
    """
    Create a filled ellipse

    Parameters
    ----------
    x0 : float
        x coordinate of the center in um.
    y0 : float
        y coordinate of the center in um.
    rX : float
        Radius of the ellipse in X direction in um.
    rY : float
        Radius of the ellipse in Y direction in um.
    rot: float
        Rotation angle (counterclockwise) in degrees. 
    layer : int, optional
        The ellipse layer. The default is 1.
    to_poly : bool, optional
        If true, the ellipse is converted to a polygon. The default is 0.
    vertices : int, optional
        Specify the number of vertices to be used for conversion to polygon.
        The default is 32.
        
    Returns
    -------
    g : GeomGroup
        A geometry containing a single ellipse.

    """
    g = GeomGroup()
    c = smsh.Ellipse(x0,y0,rX,rY,layer,rot)
    if (to_poly):
        g = c.to_polygon(vertices)
    else:
        g.add(c)
    return g

def make_ring(x0: float,y0: float,rX: float,rY: float,
              rot: float,w: float,layer: int = 1,
              to_poly: bool = 0, vertices: int = 32) -> 'GeomGroup':
    """
    Create an elliptical ring (if rX=rY a circular ring is made).
    The width should be >0.

    Parameters
    ----------
    x0 : float
        x coordinate of the center in um.
    y0 : float
        y coordinate of the center in um.
    rX : float
        Radius of the elliptical ring in X direction in um.
    rY : float
        Radius of the elliptical ring in Y direction in um.
    rot: float
        Rotation angle (counterclockwise) in degrees.
    w : float
        Ring width in um.
    layer : int, optional
        The ring layer. The default is 1.
    to_poly : bool, optional
        If true, the ring is converted to a polygon. The default is 0.
    vertices : int, optional
        Specify the number of vertices to be used for conversion to polygon.
        The default is 32.

    Returns
    -------
    g : GeomGroup
        A geometry containing a single ring.

    """
    g = GeomGroup()
    c=smsh.Ring(x0,y0,rX,rY,layer,rot,w)
    if (to_poly):
        g = c.to_polygon(vertices)
    else:
        g.add(c)
    return g

def make_arc(x0: float,y0: float,rX: float,rY: float,
              rot: float,w: float,a1: float,a2: float,
              layer: int = 1,to_poly: bool = 0, vertices: int = 32,
              split: bool = False) -> 'GeomGroup':
    """
    Create an elliptical arc (if rX=rY a circular arc is made).
    The width should be >0.
    The two angles a1 and a2 specify the initial and final angle of the arc

    Parameters
    ----------
    x0 : float
        x coordinate of the center in um.
    y0 : float
        y coordinate of the center in um.
    rX : float
        Radius of the elliptical arc in X direction in um.
    rY : float
        Radius of the elliptical arc in Y direction in um.
    rot: float
        Rotation angle (counterclockwise) in degrees.
    w : float
        Arc width in um.
    a1 : float
        Initial angle of the arc in degrees.
    a2 : float
        Final angle of the arc in degrees.
    layer : int, optional
        The arc layer. The default is 1.
    to_poly : bool, optional
        If true, the arc is converted to a polygon. The default is 0.
    vertices : int, optional
        Specify the number of vertices to be used for conversion to polygon.
        The default is 32.
    split : bool, optional
        Will also split the arc in quadrangles if to_poly is true

    Returns
    -------
    g : GeomGroup
        A geometry containing a single ring.

    """
    g = GeomGroup()
    c=smsh.Arc(x0,y0,rX,rY,layer,rot,w,a1,a2)
    if (to_poly):
        g = c.to_polygon(vertices,split)
    else:
        g.add(c)
    return g


def make_rect(x0: float,y0: float,width: float,
              height: float,numkey: int = 5,layer: int = 1) -> 'GeomGroup':
    """
    Create a rectangle centered in x0,y0.
    Optionally, the reference point x0,y0 can be any of the corners by 
    specifying a "numkey" parameter. 

    Parameters
    ----------
    x0 : float
        Reference point, x coordinate in um.
    y0 : float
        Reference point, y coordinate in um.
    width : float
        Rectangle width.
    height : float
        Rectangle height.
    layer : int, optional
        The rectangle layer. The default is 1.
    numkey : int, optional
        The reference point x0,y0 can be any of the corners or mid-points 
        specified by the numerical keypad on a standard keyboard. For example
        numkey=1 means that x0,y0 will be the lower-left corner of the 
        rectangle as 1 is located in the lower-left corner of the numerical
        keypad. Similarly, numkey=9 will be the upper-right corner.
        The default is 5 (=center).

    Returns
    -------
    r1 : GeomGroup
        A geometry containing a single rectangle.

    """
    r1 = make_poly([x0-width/2,x0+width/2,x0+width/2,x0-width/2],
                   [y0-height/2,y0-height/2,y0+height/2,y0+height/2],layer);
    if(numkey!=5):
        xoff = -((numkey-1)%3-1)
        yoff = math.floor((9-numkey)/3)-1
        r1.translate(xoff*width/2,yoff*height/2)
    
    return r1

def make_rounded_rect(x0: float,y0: float,width: float,
              height: float, corner_radius: float, resolution: int = 16,
              numkey: int = 5,layer: int = 1) -> 'GeomGroup':
    """
    Create a rectangle centered in x0,y0 with corners rounded
    Optionally, the reference point x0,y0 can be any of the corners by 
    specifying a "numkey" parameter. 

    Parameters
    ----------
    x0 : float
        Reference point, x coordinate in um.
    y0 : float
        Reference point, y coordinate in um.
    width : float
        Rectangle width.
    height : float
        Rectangle height.
    corner_radius : float
        The radius of the corners in um.
    resolution : int
        The corner resolution or number of points
    layer : int, optional
        The rectangle layer. The default is 1.
    numkey : int, optional
        The reference point x0,y0 can be any of the corners or mid-points 
        specified by the numerical keypad on a standard keyboard. For example
        numkey=1 means that x0,y0 will be the lower-left corner of the 
        rectangle as 1 is located in the lower-left corner of the numerical
        keypad. Similarly, numkey=9 will be the upper-right corner.
        The default is 5 (=center).

    Returns
    -------
    r1 : GeomGroup
        A geometry containing a single rectangle.

    """
    w0 = width
    h0 = height
    width=width-2*corner_radius
    height=height-2*corner_radius
    r1 = make_poly([x0-width/2,x0+width/2,x0+width/2,x0-width/2],
                   [y0-height/2,y0-height/2,y0+height/2,y0+height/2],layer);
    
    r1.poly_resize(corner_radius, layer, corner_radius>0, resolution*4)
    bb1 = r1.bounding_box()
    r1.scale(x0,y0,w0/bb1.width,h0/bb1.height)
    if(numkey!=5):
        xoff = -((numkey-1)%3-1)
        yoff = math.floor((9-numkey)/3)-1
        r1.translate(xoff*(width+2*corner_radius)/2,yoff*(height+2*corner_radius)/2)
    return r1

def make_tapered_path(xpts: list[float],ypts: list[float],
              widths: list[float],layer: int = 1)-> 'GeomGroup':
    """
    Creates a path with variable width. A list of path widths is given
    so that at each point the width can be changed. A polygon is produced

    Parameters
    ----------
    xpts : list[float]
        x coordinates in um.
    ypts : list[float]
        y coordinates in um.
    widths : list[float]
        path widths in um at each point (should be the same size as xpts).
    layer : int, optional
        The path layer. The default is 1.

    Returns
    -------
    g : GeomGroup
        A group containing a single path.

    """
    
    x=xpts
    y=ypts
    w=widths
    p1 = smsh.Poly([0],[0],layer)
    Npts = len(x)
    if(Npts==1):
        p1.set_points([-w[0]/2,w[0]/2,w[0]/2,-w[0]/2],
                      [-w[0]/2,-w[0]/2,w[0]/2,w[0]/2])
        p1.translate(x[0],y[0])
    if(Npts==2):
        ang1 = math.atan2(y[1]-y[0],x[1]-x[0]);
        c1 = 1/2*math.cos(ang1-math.pi/2);
        c2 = 1/2*math.cos(ang1+math.pi/2);
        s1 = 1/2*math.sin(ang1-math.pi/2);
        s2 = 1/2*math.sin(ang1+math.pi/2);
        p1.set_points([x[0]+c1*w[0],x[1]+c1*w[1],x[1]+c2*w[1],x[0]+c2*w[0]],
                      [y[0]+s1*w[0],y[1]+s1*w[1],y[1]+s2*w[1],y[0]+s2*w[0]])

    if(Npts>2):
        xp1 = []
        yp1 = []
        xp2 = []
        yp2 = []
        for j in range(1,Npts-1):
            ang1 = math.atan2(y[j]-y[j-1],x[j]-x[j-1])
            ang2 = math.atan2(y[j+1]-y[j],x[j+1]-x[j])
            d = (x[j+1]-x[j-1])*(y[j]-y[j-1])\
                - (y[j+1]-y[j-1])*(x[j]-x[j-1])
            if(j==1):
                xp1.append(x[j-1]+w[j-1]/2*math.cos(ang1-math.pi/2));
                yp1.append(y[j-1]+w[j-1]/2*math.sin(ang1-math.pi/2));
                xp2.append(x[j-1]+w[j-1]/2*math.cos(ang1+math.pi/2));
                yp2.append(y[j-1]+w[j-1]/2*math.sin(ang1+math.pi/2));
                
            if(d<0):
                xp1.append(x[j]+w[j]/2*math.cos(ang1-math.pi/2));
                yp1.append(y[j]+w[j]/2*math.sin(ang1-math.pi/2));
                xp1.append(x[j]+w[j]/2*math.cos(ang2-math.pi/2));
                yp1.append(y[j]+w[j]/2*math.sin(ang2-math.pi/2));
                wx = w[j]/2/math.cos((ang2-ang1)/2);
                a0 = math.pi/2-(ang1+ang2)/2;
                xp2.append(x[j]-wx*math.cos(a0));
                yp2.append(y[j]+wx*math.sin(a0));
            else:
                xp2.append(x[j]+w[j]/2*math.cos(ang1+math.pi/2));
                yp2.append(y[j]+w[j]/2*math.sin(ang1+math.pi/2));
                xp2.append(x[j]+w[j]/2*math.cos(ang2+math.pi/2));
                yp2.append(y[j]+w[j]/2*math.sin(ang2+math.pi/2));
                wx = w[j]/2/math.cos((ang2-ang1)/2);
                a0 = math.pi/2-(ang1+ang2)/2;
                xp1.append(x[j]+wx*math.cos(a0));
                yp1.append(y[j]-wx*math.sin(a0));
            if(j==Npts-2):
                xp1.append(x[j+1]+w[j+1]/2*math.cos(ang2-math.pi/2));
                yp1.append(y[j+1]+w[j+1]/2*math.sin(ang2-math.pi/2));
                xp2.append(x[j+1]+w[j+1]/2*math.cos(ang2+math.pi/2));
                yp2.append(y[j+1]+w[j+1]/2*math.sin(ang2+math.pi/2));
        
        xp2.reverse()
        yp2.reverse()
        p1.set_points(xp1+xp2,yp1+yp2)
    g = GeomGroup();
    g.add(p1)
    return g
    
        
