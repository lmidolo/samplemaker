"""
Basic functions to plot and inspect geometries.

These are very basic plotting functions to speed up the development of masks
and circuits. They can be used instead of writing and opening GDS files external
viewers. 
"""

import samplemaker.shapes as smsh
from samplemaker.shapes import GeomGroup
from samplemaker.devices import Device, DevicePort
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge, Polygon, Ellipse, Arrow, PathPatch
from matplotlib.widgets import Slider, Button 
from matplotlib.collections import PatchCollection
from matplotlib.textpath import TextPath
import numpy as np

_ViewerCurrentSliders= []
_ViewerCurrentDevice = None
_ViewerCurrentAxes = None

def __GeomGetPatches(grp: "GeomGroup"):
    prop_cycle = plt.rcParams['axes.prop_cycle']
    colors = prop_cycle.by_key()['color']
    patches = []
    for geom in grp.group:
        geomtype = type(geom);
        if geom.layer<0:
            continue
        lcolor = colors[np.mod(geom.layer,10)]
        if(geomtype==smsh.Poly):
            N=int(len(geom.data)/2)
            xy = np.reshape(geom.data,(N,2))
            tmpp = Polygon(xy,closed=True)
            tmpp.set_facecolor(lcolor)
            patches.append(tmpp)
            continue
        if(geomtype==smsh.Circle):
            tmpc = Circle((geom.x0, geom.y0), geom.r)
            tmpc.set_facecolor(lcolor)
            patches.append(tmpc)
            continue
        if(geomtype==smsh.Path):
            xy = np.transpose([geom.xpts,geom.ypts])
            tmpp = Polygon(xy,closed=False)
            tmpp.set_edgecolor(lcolor)
            tmpp.set_fill(False)
            patches.append(tmpp)
            continue
        if(geomtype==smsh.Text):
            print("text display is not supported, please convert to polygon first.")
            continue
        if(geomtype==smsh.SRef):
            continue
        if(geomtype==smsh.ARef):
            continue
        if(geomtype==smsh.Ellipse):
            tmpe = Ellipse((geom.x0,geom.y0),geom.r*2,geom.r1*2,angle=geom.rot)
            tmpe.set_facecolor(lcolor)
            patches.append(tmpe)
            continue
        if(geomtype==smsh.Ring):
            gpl = geom.to_polygon()
            geom=gpl.group[0]
            N=int(len(geom.data)/2)
            xy = np.reshape(geom.data,(N,2))
            tmpp = Polygon(xy,closed=True)
            tmpp.set_facecolor(lcolor)
            patches.append(tmpp)
            continue
        if(geomtype==smsh.Arc):
            gpl = geom.to_polygon()
            geom=gpl.group[0]
            N=int(len(geom.data)/2)
            xy = np.reshape(geom.data,(N,2))
            tmpp = Polygon(xy,True)
            tmpp.set_facecolor(lcolor)
            patches.append(tmpp)
            continue
    return patches

def __GetPortPatches(port: DevicePort):
    if port.name=="":
        return []
    patches = []
    patches.append(Arrow(port.x0,port.y0,port.dx(),port.dy()))
    tpath = TextPath([port.x0,port.y0], port.name, size=1)
    patches.append(PathPatch(tpath))
    return patches
    
def __GetDevicePortsPatches(dev: Device):
    patches = []
    for port in dev._ports.values():
        patches+=__GetPortPatches(port)
    
    return patches
    
    
def GeomView(grp: GeomGroup):
    """
    Plots a geometry in a matplotlib window.
    Only polygons and circles are displayed. Most elements are either 
    ignored or converted to polygon.
    No flattening is performed, thus structure references are not displayed.

    Parameters
    ----------
    grp : samplemaker.shapes.GeomGroup
        The geometry to be displayed.

    Returns
    -------
    None.

    """
    plt.close('all')
    fig, ax = plt.subplots()
    patches = __GeomGetPatches(grp)
    p = PatchCollection(patches, match_original=True)
    ax.add_collection(p)
    plt.grid()
    plt.axis('equal')
    plt.show()


def __update_scrollbar(val):
    global _ViewerCurrentDevice
    global _ViewerCurrentSliders
    global _ViewerCurrentAxes
    dev = _ViewerCurrentDevice
    pn = 0
    for param in dev._p.keys():
        #print(_ViewerCurrentSliders[pn].val)
        dev.set_param(param, _ViewerCurrentSliders[pn].val)
        pn = pn+1

        
    #xlim = _ViewerCurrentAxes.get_xlim()
    #ylim = _ViewerCurrentAxes.get_ylim()
    dev.use_references=False
    dev.initialize()
    geomE=dev.run()
    bb = geomE.bounding_box()
    #geomE=geomE.flatten()
    patches = __GeomGetPatches(geomE)
    patches+=__GetDevicePortsPatches(dev)
    p = PatchCollection(patches, match_original=True)
    _ViewerCurrentAxes.clear()
    _ViewerCurrentAxes.add_collection(p)
    _ViewerCurrentAxes.grid(True)
    _ViewerCurrentAxes.set_xlim([bb.llx,bb.urx()])
    _ViewerCurrentAxes.set_ylim([bb.lly,bb.ury()])
    _ViewerCurrentAxes.aspect='equal'
    _ViewerCurrentAxes.set_title(dev._name)
    
 

def DeviceInspect(devcl: Device):
    """
    Interactive display of devices defined from `samplemaker.devices`.
    The device is rendered according to the default parameters.
    Additionally a set of scrollbars is created to interactively modify 
    the parameters and observe the changes in real time.
    If the device includes ports, they are displayed as blue arrows.    
    
    Parameters
    ----------
    devcl : samplemaker.devices.Device
        A device object to be displayed.

    Returns
    -------
    None.

    """
    global _ViewerCurrentDevice
    global _ViewerCurrentSliders
    global _ViewerCurrentAxes
    dev = devcl.build()
    _ViewerCurrentDevice= dev;
    geomE=dev.run()
    geomE=geomE.flatten()
    plt.close('all')
    fig, ax = plt.subplots()
    patches = __GeomGetPatches(geomE)
    patches+=__GetDevicePortsPatches(dev)
    p = PatchCollection(patches, match_original=True)
    ax.add_collection(p)
    _ViewerCurrentAxes = ax
    plt.grid()
    plt.axis('equal')
    plt.title(dev._name)
    plt.subplots_adjust(bottom=0.5)
    _ViewerCurrentSliders = []
    Np = len(dev._p.keys())
    pn = 0;
    for param in dev._p.keys():
        ax_amp = plt.axes([0.25, 0.05+pn*1.0/Np*0.35, 0.65, 0.03])
        minv = 0
        maxv = dev._p[param]*10
        prange = dev._prange[param]
        if(prange[1] != np.inf):
            maxv = prange[1]
        if(prange[0] != 0):
            minv = prange[0]
            
        valstep = dev._p[param]/10;
        if(valstep==0):
            valstep=0.1;
        if dev._ptype[param]==int:
            maxv = int(maxv)
            valstep = 1
        if dev._ptype[param]==bool:
            maxv = 1
            valstep = 1
        if(maxv==0): 
            maxv=1;
        samp = Slider(
            ax_amp,  param, minv, maxv,
            valinit=dev._p[param],
            color="green",
            valstep=valstep
            )
        samp.on_changed(__update_scrollbar)
        #cb = lambda x: onclick(x,param)
        #samp.connect_event('button_press_event', cb)
        _ViewerCurrentSliders.append(samp)
        pn = pn+1
    
    plt.show()
    #return sliders
    
    