"""
Base waveguide library. 


Implements a simple waveguide sequencer and optical ports.
This module can be used as template to develop different waveguide libraries.

"""

import math
from copy import deepcopy
import numpy as np
from samplemaker.devices import DevicePort
from samplemaker.shapes import GeomGroup
import samplemaker.sequencer as smseq
import samplemaker.makers as sm
from samplemaker.routers import WaveguideConnect

# First step in defining a waveguide library is to define a sequencer
# and its dictionary.

# Let's define some options for the BaseWaveguide sequencer
def BaseWaveguideOptions():
    BaseWaveguidesOptions = smseq.default_options()
    # Let's define the default waveguide layer
    BaseWaveguidesOptions["wgLayer"] = 1
    # For waveguide bends, let's use a fixed resolution
    BaseWaveguidesOptions["bendResolution"] = 30
    # Let's define the default waveguide width
    BaseWaveguidesOptions["defaultWidth"] = 0.3
    return BaseWaveguidesOptions

# Let's define the sequencer state class
# We could use the default, but we would like to store
# the current waveguide width as well using the parameter 'w'
class BaseWaveguideState(smseq.SequencerState):
    def __init__(self):
        """
        The sequencer state for BaseWaveguide library.
        Defines 'w' as current waveguide width. 

        Returns
        -------
        None.

        """
        super().__init__()
        self.state["w"]=0 # The value will be set by the INIT command

# Let's define the INIT command, which is always the first to execute
def BaseWaveguideINIT(state, options):
    smseq.__initState(state,options)
    if(not options["__no_init__"]):
        state['w'] = options['defaultWidth']
    
# The S command to go straight
def BaseWaveguideS(args,state,options)->GeomGroup:
    """
    Draw straight waveguide

    Parameters
    ----------
    args : list
        1 argument: waveguide length.
    state : dict
        Current state.
    options : dict
        The sequencer options.

    Returns
    -------
    samplemaker.shapes.GeomGroup
        The waveguide geometry.

    """
    dist = args[0]
    if(dist==0):
        return GeomGroup()
    
    # Let's draw a simple rectangle
    wg = sm.make_rect(0,0,dist,state['w'],numkey=4,layer=options["wgLayer"])
    # Now rotate and translate according to pointer orientation
    wg.rotate_translate(state['x'], state['y'], state['a'])
    # Finally, update the state
    state['x']+=dist*math.cos(math.radians(state['a']))
    state['y']+=dist*math.sin(math.radians(state['a']))
    state['__OL__']+=dist
    return wg

# The B command to make a circular bend
def BaseWaveguideB(args,state,options)->GeomGroup:
    """
    Draw circular bend waveguide

    Parameters
    ----------
    args : list
        2 arguments: angle of bend (in degrees), radius of bend.
    state : dict
        Current state.
    options : dict
        The sequencer options.

    Returns
    -------
    samplemaker.shapes.GeomGroup
        The waveguide geometry.

    """
    angle = args[0]
    radius = args[1]
    if(angle==0):
        return GeomGroup()
    
    wg = sm.make_arc(0, radius, radius, radius, 
                -90, state['w'], 0, abs(angle),
                vertices=options["bendResolution"],
                to_poly=True,layer=options["wgLayer"])  
    xf = radius*math.sin(math.radians(abs(angle)))
    yf = radius*(1-math.cos(math.radians(abs(angle))))
    if(angle<0):
        wg.mirrorY(0)
        yf=-yf
    ept = sm.make_dot(xf, yf) # helps calculating the end point
    # Now rotate and translate according to pointer orientation
    wg.rotate_translate(state['x'], state['y'], state['a'])
    ept.rotate_translate(state['x'], state['y'], state['a'])
    # Finally, update the state
    state['x']=ept.x
    state['y']=ept.y
    state['a']+=angle
    state['__OL__']+=radius*2*math.pi/360*abs(angle)
    
    return wg

def BaseWaveguideC(args, state, options)->GeomGroup:
    """
    Draw cosine bend waveguide. While keeping the same direciton,
    bend the waveguide using a cosine function.

    Parameters
    ----------
    args : list
        2 arguments: offset (in um), radius of bend.
    state : dict
        Current state.
    options : dict
        The sequencer options.

    Returns
    -------
    samplemaker.shapes.GeomGroup
        The waveguide geometry.

    """
    off = args[0]
    radius = args[1]
    delta = 0.01 # at the very beginning and at the end go straight by delta
    radius -= delta
    if(radius ==0):
        return GeomGroup()
    N = options['bendResolution']
    amp = math.pi*off/4/radius
    t = np.linspace(0,2,N);
    s = [math.asin(math.tan(math.atan(amp)*x)/amp) for x in t if x<1]
    s+= [math.asin(math.tan(math.atan(amp)*(x-2))/amp)+math.pi for x in t if x>=1]
    s = np.array(s)
    xpts = s/math.pi*2*radius + state['x']
    ypts = off*(np.cos(s+math.pi)+1)/2 + state['y']
    xpts = np.append(xpts[0],xpts+delta)
    xpts = np.append(xpts,xpts[-1]+delta)
    ypts = np.append(ypts[0],ypts)
    ypts = np.append(ypts,ypts[-1])
    OL = np.sum(np.sqrt(np.power(np.ediff1d(xpts),2)+np.power(np.ediff1d(ypts),2)))
    wg = sm.make_path(xpts, ypts, state['w'],to_poly=1,layer=options["wgLayer"])
    outdot = sm.make_dot(xpts[-1],ypts[-1])
    wg.rotate(state['x'],state['y'],state['a'])
    outdot.rotate(state["x"],state["y"],state["a"])
    state['x']=outdot.x
    state['y']=outdot.y
    state["__OL__"]+=OL
    return wg    

def BaseWaveguideT(args, state, options)->GeomGroup:
    """
    Draw linear taper

    Parameters
    ----------
    args : list
        2 arguments: length of taper (in um), final width (if <0, the defaultWidth value is used).
    state : dict
        Current state.
    options : dict
        The sequencer options.

    Returns
    -------
    samplemaker.shapes.GeomGroup
        The waveguide geometry.

    """
    dist = args[0]
    wf = args[1]
    if(dist==0):
        return GeomGroup()
    if(wf < 0): wf = options["defaultWidth"]
    a = math.radians(state['a'])
    xf = state['x']+dist*math.cos(a)
    yf = state['y']+dist*math.sin(a)
    wg = sm.make_tapered_path([state['x'],xf], [state['y'],yf], [state['w'],wf],
                              layer=options["wgLayer"])
    state['x']=xf
    state['y']=yf
    state['w']=wf
    state["__OL__"]+=dist
    return wg
    
def BaseWaveguideOFF(args,state,options)->GeomGroup:
    """
    Offset the waveguide (jumps left or right of waveguide)

    Parameters
    ----------
    args : list
        1 argument: offset (in um), positive means on left of waveguide direction.
    state : dict
        Current state.
    options : dict
        The sequencer options.

    Returns
    -------
    samplemaker.shapes.GeomGroup
        The waveguide geometry.

    """
    off = args[0]
    a = math.radians(state['a']+90)
    state['x']+=off*math.cos(a)
    state['y']+=off*math.sin(a)
    return GeomGroup()

def BaseWaveguideCommands() -> dict:
    """
    Creates the dictionary with the command list and corresponding
    functions.

    Returns
    -------
    dict
        The command list to be used by the sequencer.

    """
    command_list=smseq.default_command_list()
    command_list["INIT"] = (0,BaseWaveguideINIT)
    command_list["S"] = (1,BaseWaveguideS)
    command_list["B"] = (2,BaseWaveguideB)
    command_list["C"] = (2,BaseWaveguideC)
    command_list["T"] = (2,BaseWaveguideT)
    command_list["OFF"] = (1,BaseWaveguideOFF)
    return command_list

# Finally, create a custom sequencer
class BaseWaveguideSequencer(smseq.Sequencer):
    def __init__(self,seq):
        """
        Creates a custom sequencer for simple waveguides.

        Parameters
        ----------
        seq : list
            The sequence to be executed.

        Returns
        -------
        None.

        """
        opts = BaseWaveguideOptions()
        state  = BaseWaveguideState()
        cmds = BaseWaveguideCommands()
        super().__init__(seq,opts,state,cmds)


# some global connector options
BaseWaveguideConnectorOptions = {"bending_radius":3,
                          "sequencer_options":BaseWaveguideOptions()}

def BaseWaveguideConnector(port1: DevicePort,port2: DevicePort) -> GeomGroup:
    res = WaveguideConnect(port1, port2,BaseWaveguideConnectorOptions["bending_radius"])
    if(res[0]==True):
        so = BaseWaveguideSequencer(res[1])
        so.options = deepcopy(BaseWaveguideConnectorOptions["sequencer_options"])
        g = so.run()
        g.rotate_translate(port1.x0,port1.y0,math.degrees(port1.angle()))
        return g
    else:
        return GeomGroup()

# Now let's create a new DevicePort with a connector function
class BaseWaveguidePort(DevicePort):
    def __init__(self,x0: float, y0 : float,orient: str ="East",width: float =None,name: str =None):
        orient = orient.lower()
        horizontal = True
        forward = True
        if(orient=="west" or orient=="w"):
            forward=False
        if(orient=="north" or orient=="n"):
            horizontal=False
        if(orient=="south" or orient=="s"):
            horizontal=False
            forward=False
            
        super().__init__(x0,y0,horizontal,forward)
        self.width = width
        self.name=name
        self.connector_function=BaseWaveguideConnector
    