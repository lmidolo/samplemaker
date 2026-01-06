"""
Classes for drawing photonic crystals and periodic sturctures.

Crystals
--------
Crystals are periodic structures arranged in two dimensions. They are defined by
a unit cell and a set of lattice sites (usually with some periodicity)

In this module, a unit cell is given by a user-provided function that takes parameters 
as input (e.g. the radius of a circle) and produces a geometry.

For example the default unit cell function is a circle defined as:

    def __circ_cellfun__(x,y,params):
    if params=="test":
        return 1
    else:
        return sm.make_circle(x, y, params[0], 0)

The `Crystal` class provides a template for periodic structures consisting of an 
array of lattice sites (coordinates) in normalized units and a list of parameters
to be passed to the unit cell function.
Thus a crystal is created by multiple calls to the unit cell function.
Note that the unit cell function can also return references to another cell, for example
a cell that contains a single circle. 

Two make_ functions are provided to create a samplemaker.shapes.GeomGroup object
with the designed parameters.

"""

import samplemaker.makers as sm
from samplemaker.shapes import GeomGroup
import math
import numpy as np
from samplemaker.layout import LayoutPool
from copy import deepcopy

class Crystal:
    def __init__(self,xpts: list[float] =[],ypts: list[float] = [],params: list[float]=[]):
        """
        Initialize a Crystal template.


        Parameters
        ----------
        xpts : list[float], optional
            List of x-coordinates (normalized) of the lattice sites. The default is [].
        ypts : list[float], optional
            List of y-coordinates (normalized) of the lattice sites. The default is [].
        params : list[float], optional
            2D list of paramter values of the lattice sites. Should be of the form params[pindex,site_index]. 
            The default is [].

        Returns
        -------
        None.

        """
        self.xpts = xpts
        self.ypts = ypts
        if(type(params)==np.ndarray):
            params=np.float64(params)
        self.params = params
        
    def remove_at_index(self, index: list[int]):
        """
        Removes lattice sites from a list of indices

        Parameters
        ----------
        index : list[int]
            indexes to be removed from the list used to initialize the crystal.

        Returns
        -------
        None.

        """
        if len(index)>0:  
            self.xpts=np.delete(self.xpts, index)
            self.ypts=np.delete(self.ypts, index)
            self.params=np.delete(self.params, index,axis=1)
    
    def shift_at_index(self, index: list[int], shift_x: float, shift_y: float,
                       relative: bool = False, orig_x: float = 0, orig_y: float = 0):
        """
        Shifts the lattice sites specified in the list

        Parameters
        ----------
        index : list[int]
            A list of indexes to be shifted.
        shift_x : float
            x-amount of shift (in normalized units).
        shift_y : float
            y-amount of shift (in normalized units).
        relative : bool, optional
            Perform a relative shift from the origin. The default is False.
        orig_x : float, optional
            x-coordinate of the origin of shift (if relative). The default is 0.
        orig_y : float, optional
            y-coordinate of the origin of shift (if relative). The default is 0.

        Returns
        -------
        None.

        """
        if len(index)>0:
            if(relative):               
                self.xpts[index] = self.xpts[index]+(2.0*(self.xpts[index]>orig_x)-1)*shift_x
                self.ypts[index] = self.ypts[index]+(2.0*(self.ypts[index]>orig_y)-1)*shift_y
            else:
                self.xpts[index] = self.xpts[index]+shift_x
                self.ypts[index] = self.ypts[index]+shift_y
    
    def param_at_index(self, index: int, pindex: int, pvalues: float):
        """
        Sets a parameter at the lattice index. 

        Parameters
        ----------
        index : int
            The lattice index.
        pindex : int
            The parameter index.
        pvalues : float
            The new value of the paramter to be set.

        Returns
        -------
        None.

        """
        if len(index)>0:
            self.params[pindex,index]=pvalues

    
    def coord_to_index(self,xc,yc):
        """
        Converts a coordinate to an index (if matches).

        Parameters
        ----------
        xc : float
            x-coordinate(s) in normalized units.
        yc : float
            y-coordinate(s) in normalized units.

        Returns
        -------
        sel : list[float]
            A list of coordinate indices.

        """
        if(type(xc)!=np.ndarray):
            xc = np.array(xc)
            yc = np.array(yc)
        sel = []
        for i in range(xc.size):
            sx = abs(self.xpts-xc[i])<1e-6
            sy = abs(self.ypts-yc[i])<1e-6
            res = np.where(sx&sy);
            if(res[0].size)==0: 
                print("defect_at_coord(): warning, no match for ",xc[i],yc[i])
            else:
                sel.append(res[0][0])
        return sel
    
    def remove_crystal(self, crystal: "Crystal"):
        """
        Subtracts a crystal from another crystal. 

        Parameters
        ----------
        crystal : Crystal
            Another crystal whose lattice sites will be removed.

        Returns
        -------
        None.

        """
        self.remove_at_index(self.coord_to_index(crystal.xpts, crystal.ypts))      
        
    def add_crystal(self, crystal: "Crystal"):
        """
        Adds a crystal to the current crystal.

        Parameters
        ----------
        crystal : Crystal
            Another crystal to be added to the existing one.

        Returns
        -------
        None.

        """
        self.xpts = np.append(self.xpts,crystal.xpts)
        self.ypts = np.append(self.ypts,crystal.ypts)
        self.params = np.append(self.params,crystal.params,axis=1)
        
    
    def copy(self):
        """
        Create a deep copy of the crystal.

        Returns
        -------
        Crystal
            A deepcopy of crystal.

        """
        return deepcopy(self)
    
    @classmethod
    def triangular_hexagonal(cls,N: int, filled: bool, Nparams: int = 1):
        """
        Creates a triangular photonic crystal in the shape of a hexagon, often
        useful for point-defect cavities.

        Parameters
        ----------
        cls : Crystal
            The Crystal class.
        N : int
            Number of lattice sites extending in the radial direction (0 means one hole in the center).
        filled : bool
            If True, creates a filled hexagonal crystal, otherwise a ring of radius N.
        Nparams : int, optional
            Number of parameters to be controlled for each lattice site. 
            The default is 1.

        Returns
        -------
        Crystal
            A crystal object with the pre-compiled lattice sites.

        """
        if(N==0):
            return cls(np.array([0]),np.array([0]),np.ones((Nparams,1)))
        xpts = np.array([])
        ypts = np.array([])
        
        if(filled):
            for i in range(0,N):
                tmpc = cls.triangular_hexagonal(i,False)
                xpts = np.append(xpts,tmpc.xpts)
                ypts = np.append(ypts,tmpc.ypts)
        else:        
            th = np.array([e for e in range(0,361,60)])
            cx = N*np.cos(np.radians(th))
            cy = N*np.sin(np.radians(th))
            for i in range(6):
                xint = np.linspace(cx[i],cx[i+1],N+1)
                m = (cy[i+1]-cy[i])/(cx[i+1]-cx[i])
                yint = m*(xint[0:-1:]-cx[i])+cy[i]
                xpts = np.append(xpts,xint[0:-1:])
                ypts = np.append(ypts,yint)
            
        params = np.ones((Nparams,xpts.size));
        return cls(xpts,ypts,params)    
    
    @classmethod
    def triangular_box(cls,Nx: int,Ny: int, Nparams: int = 1):
        """
        Creates a triangular photonic crystal in the shape of a rectangular 
        box. 

        Parameters
        ----------
        cls : Crystal
            The class.
        Nx : int
            Number of holes in the x direction, the crystal will span from
            -Nx to Nx (double size).
        Ny : int
            Number of holes in the y direction, note that we consider Ny=1 the
            row where y=sqrt(3). The crystal will span from -Ny to Ny.
        Nparams : int, optional
            Number of parameters to be controlled for each lattice site. 
            The default is 1.

        Returns
        -------
        Crystal
            A crystal object with the pre-compiled lattice sites.

        """
        if(Nx==0 & Ny==0):
            return cls(np.array([0]),np.array([0]),np.ones((Nparams,1)))
        
        x1 = np.array([e for e in range(-Nx,Nx+1)])
        y1 = np.array([e*math.sqrt(3) for e in range(-Ny,Ny+1)])
        x2 = np.array([e+0.5 for e in range(-Nx,Nx)])
        y2 = np.array([math.sqrt(3)/2+math.sqrt(3)*e for e in range(-Ny,Ny)]);
        X1,Y1 = np.meshgrid(x1,y1)
        X2,Y2 = np.meshgrid(x2,y2)
        xpts = np.append(X1.reshape(-1),X2.reshape(-1))
        ypts = np.append(Y1.reshape(-1),Y2.reshape(-1))
        params = np.ones((Nparams,xpts.size));
        return cls(xpts,ypts,params)
    
    @classmethod
    def triangular_heterophc(cls,Nx: float, Ny: float, 
                             spacing: list[float], periods: list[int],
                             Nparams: int = 1):
        """
        Creates a triangular photonic crystal in the shape of a rectangular 
        box using a heterostructure.

        Parameters
        ----------
        cls : Crystal
            The class.
        Nx : int
            Number of holes in the x direction, the crystal will span from
            -Nx to Nx (double size).
        Ny : int
            Number of holes in the y direction, note that we consider Ny=1 the
            row where y=sqrt(3). The crystal will span from -Ny to Ny.
        spacing : list[float]
            Array of lattice constants to be used for the various sections of the hetero phc.
        periods : list[int]
            How many times should each spacing be repeated (always end with 1 for the remaining).
        Nparams : int, optional
            Number of parameters to be controlled for each lattice site. 
            The default is 1.
            
        Returns
        -------
        heterophc : Crystal
            A crystal object with the pre-compiled lattice sites.

        """
        startx=0
        x1=[]
        x2=[]
        a = spacing
        totalp=np.sum(periods)
        Nxorig = Nx
        Nx = math.ceil(Nx)
    
        for i in range(len(a)):
            xchunk1=startx+np.array([e for e in range(0,periods[i]+1)])*a[i]
            xchunk2=startx+(0.5+np.array([e for e in range(0,periods[i])]))*a[i]
            startx=xchunk1[-1]
            x1=np.append(x1,xchunk1)
            x2=np.append(x2,xchunk2)
  
        x1=np.append(x1,startx+np.array([e for e in range(0,int(Nx-totalp+1))]));
        x2=np.append(x2,startx+(0.5 + np.array([e for e in range(0,int(Nx-totalp))])))
        x1=np.append(x1,-x1[::-1])
        x2=np.append(x2,-x2[::-1])
        x1=np.sort(np.unique(x1))
        x2=np.sort(np.unique(x2))
        y1 = np.array([e*math.sqrt(3) for e in range(-Ny,Ny+1)])
        y2 = np.array([math.sqrt(3)/2+math.sqrt(3)*e for e in range(-Ny,Ny)]);
        X1,Y1 = np.meshgrid(x1,y1)
        X2,Y2 = np.meshgrid(x2,y2)
        xpts = np.append(X1.reshape(-1),X2.reshape(-1))
        ypts = np.append(Y1.reshape(-1),Y2.reshape(-1))
        params = np.ones((Nparams,xpts.size));
        heterophc = cls(xpts,ypts,params)
        if (Ny != 0):
            heterophc.remove_crystal(cls.triangular_heterophc(Nx, 0, a, periods))

        # Get rid of extra final holes if fraction Nx
        if (Nxorig-Nx < 0):
            maxx = np.max(heterophc.xpts);
            minx = np.min(heterophc.ypts);
            sx1 = heterophc.xpts>(maxx-0.1)
            sx2 = heterophc.xpts<(minx+0.1)
            sel = np.where(sx1|sx2)
            heterophc.remove_at_index(sel)
        
        return heterophc

def __circ_cellfun__(x,y,params):
    if params=="test":
        return 1
    else:
        return sm.make_circle(x, y, params[0], 0)

def __circref_cellfun__(x,y,params):
    if params=="test":
        return 1
    else:
        return sm.make_sref(x, y, "_CIRCLE",LayoutPool["_CIRCLE"],mag=params[0])

def make_phc(crystal: "Crystal", scaling: float, cellparams: list[float], x0: float, y0: float, 
             cellfun = __circ_cellfun__, name: str = ""):
    """
    Creates a photonic crystal geometry

    Parameters
    ----------
    crystal : "Crystal"
        The crystal template.
    scaling : float
        An overall scaling factor in um.
    cellparams : list[float]
        A list with the scaling parameters to be passed to the cell function.
    x0 : float
        Position x-coordinate in um.
    y0 : float
        Position y-coordinate in um.
    cellfun : TYPE, optional
        A function of the type fun(x,y,params) that returns the geometry of the unit cell.
        It should also return the number of parameters required to draw the unit cell if "test" is passed as params. 
        The default is __circ_cellfun__.
    name : str, optional
        Name of the crystal. The default is "".

    Returns
    -------
    phc : GeomGroup
        A geometry containing the full crystal.

    """
    nargs = cellfun(0,0,"test");
    phc = GeomGroup();
    for i in range(len(crystal.xpts)):
        xpos = crystal.xpts[i]*scaling
        ypos = crystal.ypts[i]*scaling
        params = [0.]*nargs
        for j in range(nargs):
            params[j] = crystal.params[j,i]*cellparams[j]
        phc+=cellfun(xpos,ypos,params)   
        
    phc.translate(x0,y0)
    return phc

def make_phc_inpoly(crystal: "Crystal", poly: "sm.Poly", scaling: float, cellparams: list[float], 
                    x0: float, y0: float, cellfun = __circ_cellfun__, name: str = ""):
    """
    Creates a photonic crystal geometry clipped inside a polygon area.

    Parameters
    ----------
    crystal : "Crystal"
        The crystal template.
    poly: "Poly"
        The polygon used to clip. Should be created with samplemaker.shapes.Poly
    scaling : float
        An overall scaling factor in um.
    cellparams : list[float]
        A list with the scaling parameters to be passed to the cell function.
    x0 : float
        Position x-coordinate in um.
    y0 : float
        Position y-coordinate in um.
    cellfun : TYPE, optional
        A function of the type fun(x,y,params) that returns the geometry of the unit cell.
        It should also return the number of parameters required to draw the unit cell if "test" is passed as params. 
        The default is __circ_cellfun__.
    name : str, optional
        Name of the crystal. The default is "".

    Returns
    -------
    phc : GeomGroup
        A geometry containing the full crystal.

    """
    nargs = cellfun(0,0,"test");
    phc = GeomGroup();
    for i in range(len(crystal.xpts)):
        xpos = crystal.xpts[i]*scaling
        ypos = crystal.ypts[i]*scaling
        if(poly.point_inside(xpos,ypos)):
            params = [0.]*nargs
            for j in range(nargs):
                params[j] = crystal.params[j,i]*cellparams[j]
            phc+=cellfun(xpos,ypos,params)   
        
    phc.translate(x0,y0)
    return phc
    

