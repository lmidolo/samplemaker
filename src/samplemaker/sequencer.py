"""
Classes to handle custom sequences of shapes (e.g. waveguides).

The concept of sequence
-----------------------

A sequence in `samplemaker` is a list of instructions to be executed in sequence
that act on a drawing state machine.
The machine is initialized with some internal setting and each instruction can 
modify the internal settings of the machine. Moreover, it is expected that
some of the instruction actually return a geometry that is eventually drawn 
on screen, but that is not necessary.

While the above description might sound abstract, the sequencer is nothing more
than a compiler of a short code with user-defined instructions.
It becomes very handy when designing waveguides.

Each instruction is built as a list contaning a text command followed by an arbitrary
number of parameters (or function arguments). 
For example, one simple sequence of commands is

    seq = [['S',3], ['B', 90, 3]]
    
It contains two instructions. The first is the command 'S' with just one argument
and the second is the command 'B' with two arguments.

The sequencer requires the user to provide a set of functions to be called when
the instruction is recognized. For example 'S' can be associated to the 'go straight'
command and a function 

    def S_command(args,state,options):
        # Draw something based on the machine state, options and args.
        seq.state['x']+=args[0] # Modify the state
    
    seq_dictionary=dict()
    seq_dictionary['S']= (1, S_command) # tells the sequencer to call S_command whenever the 'S' instruction is encountered.

The sequencer offers a template-based programming of arbitrary sequences.
In this way, the same sequence can be used with different dictionaries and result
in different geometries that use the same conceptual instructions.

When is this useful? Mostly when using routines that automatically perform 
routing between parts of the design (e.g. waveguide routing). If the function
returns a sequence instead of an actual geometry, the same routing function
can be used for different circuit design platforms.

Additionally, the level of automation in circuit design can be highly improved, as
some functions can be 'smart' and perform specific actions depending on the current
machine state. 

The best way to learn how to master sequencers is to look at the tutorials distributed
with `samplemaker`. 

"""

import samplemaker.makers as sm
from samplemaker.shapes import GeomGroup
from samplemaker.devices import _DeviceList
import math
import numpy as np
from copy import deepcopy

def __changeState(args,state,options):
    state[args[0]]=args[1]
    return GeomGroup()

def __centerState(args,state,options):
    state['__XC__']=-state["x"]+args[0]
    state['__YC__']=-state["y"]+args[1]
    return GeomGroup()

def __storeState(args,state,options):
    state['STORED']+=[[state["x"],state["y"]]] 
    return GeomGroup()

def __initState(state,options):
    if(not options["__no_init__"]):
        state["x"]=0
        state["y"]=0
        state["a"]=0
        state["__OL__"]=0 # Optical length
        state["__XC__"]=0
        state["__YC__"]=0
        state["STORED"]=[]
        

def __insertDevice(args,state,options):
    devname = args[0]
    inport = args[1]
    outport = args[2]
    if devname in _DeviceList:
        dev = _DeviceList[devname].build()
        # pass the local parameters now
        dev._p = options["dev_"+devname]
        if(hasattr(dev,"_seq")):
            dev._seq.state = deepcopy(state)
            dev._seq.options = deepcopy(options)
        g = dev.run()
        if(inport in dev._ports and outport in dev._ports):
            p1 = dev._ports[inport]
            xd = p1.x0
            yd = p1.y0
            ad = math.degrees(p1.angle())+180
            p2 = dev._ports[outport]
            xdo = p2.x0
            ydo = p2.y0
            ado = math.degrees(p2.angle())
            g.rotate(xd,yd,-ad+state["a"])
            g.translate(state['x']-xd,state['y']-yd)
            state['x']+=(xdo-xd)*math.cos(math.radians(state["a"]-ad))\
                - (ydo-yd)*math.sin(math.radians(state["a"]-ad))
            state['y']+=(xdo-xd)*math.sin(math.radians(state["a"]-ad))\
                    + (ydo-yd)*math.cos(math.radians(state["a"]-ad))
            state['a']+=ado
        else:
            print("Warning: device has no port called", inport, "or", outport)
        return g
    else:
        print("No device found with name",devname)
    return GeomGroup()

def default_command_list():
    """
    Creates a basic dictionary with basic commands required by the sequencer.
    These include
    
    * STATE: change the state variable to something else
    * CENTER: forces the current position state to change
    * STORE: stores the current position state
    * DEV: Inserts a device at the current postion

    Returns
    -------
    defcmdlist : dict
        The default command dictionary.

    """
    defcmdlist = dict()
    defcmdlist["INIT"] = (0,__initState)
    defcmdlist["STATE"] = (2,__changeState)
    defcmdlist["CENTER"] = (2,__centerState)
    defcmdlist["STORE"] = (0,__storeState)
    defcmdlist["DEV"] = (3,__insertDevice)
    return defcmdlist

def default_options():
    """
    Default options for the sequencer.
    This returns the essential base options.

    Returns
    -------
    defopts : dict
        Returns the default options for the sequencer.

    """
    defopts = dict()
    for dname in _DeviceList:
        dev = _DeviceList[dname]()
        dev.parameters()
        defopts["dev_"+dname] = dev._p
        
    defopts["__no_init__"] = False # Disable INIT command 
    return defopts        

class SequencerState:
    def __init__(self):
        """
        Initialize a sequencer state to default values.
        The default sequencer state contains the following variables:
            
        * 'x': The current x-coordinate of the sequencer. Initially 0
        * 'y': The current y-coordinate of the sequencer. Initially 0
        * 'a': The current angle (or orientation) of the sequencer. Initially 0 (east)
        * '__OL__': Stores the accumulated distance.
        * '__XC__': Stores the current x-coordinate when calling 'CENTER'
        * '__YC__': Stores the current y-coordinate when calling 'CENTER'
        * 'STORED': Stores the current position when calling 'STORE'

        Returns
        -------
        None.

        """
        self.state = dict()
        self.state["x"]=0
        self.state["y"]=0
        self.state["a"]=0
        self.state["__OL__"]=0 # Optical length
        self.state["__XC__"]=0
        self.state["__YC__"]=0
        self.state["STORED"]=[]
        
    
class Sequencer:
    def __init__(self,seq,
                 seq_options: dict,
                 seq_state: SequencerState,
                 seq_dictionary: dict):
        """
        Initializes a new sequencer object. It requires a sequence, an option
        dictionary, a state object, and a dictionary to interpret commands.

        Parameters
        ----------
        seq : List
            The sequence to be executed (list of instructions).
        seq_options : dict
            Dictionary with all the options to be passed to instructions.
        seq_state : SequencerState
            SequencerState object with the initial state of the sequencer.
        seq_dictionary : dict
            The dictionary with instructions.

        Returns
        -------
        None.

        """
        self.seq = seq
        self.options = seq_options
        self.dic = seq_dictionary
        self.state = seq_state.state
        self.debug_state = False
    
    def set_debug_state(self,value: bool):
        """
        Sets debug mode. In debug mode the state is printed at all steps.

        Parameters
        ----------
        value : bool
            True to set debug mode on.

        Returns
        -------
        None.

        """
        self.debug_state=value
    
    def get_state(self):
        """
        The current state of the sequencer

        Returns
        -------
        SequencerState
            Returns the SequencerState object.

        """
        return deepcopy(self.state)
    
    def reset(self):
        """
        Resets the sequencer position state to 0,0
        and sets direction back to zero.

        Returns
        -------
        None.

        """
        self.state["x"]=0
        self.state["y"]=0
        self.state["a"]=0
    
    def run(self):
        """
        Execute the sequence and get the final geometry object.

        Returns
        -------
        g : samplemaker.shapes.GeomGroup
            The resulting geometry.

        """
        g = GeomGroup();
        self.dic["INIT"][1](self.state,self.options)
        for instr in self.seq:
            if(len(instr)==0): continue
            cmd = instr[0]
            args = instr[1:]
            if cmd in self.dic:
                action = self.dic[cmd]
                if(action[0]!=len(args)):
                    print("Wrong number of arguments for command ",cmd)
                    break
                else:
                    g += action[1](args,self.state,self.options)
                    if self.debug_state:
                        print('self state ',self.state)
            else:
                print("Command ", cmd, " does not exist")
                break
        g.translate(self.state["__XC__"],self.state["__YC__"])
        self.state["x"]+=self.state["__XC__"]
        self.state["y"]+=self.state["__YC__"]
        for coords in self.state["STORED"]:
            coords[0]+=self.state["__XC__"]
            coords[1]+=self.state["__YC__"]
        if self.debug_state:
            print('final state ',self.state)
            
        return g