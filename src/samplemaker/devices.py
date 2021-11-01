# -*- coding: utf-8 -*-
"""
This module contains the base classes for generating re-usable device classes.

The Device class
----------------
The `Device` class is an interface to generate specific devices. 
In `samplemaker` a device is the combination of drawing commands that generate
a specific pattern which is typically re-used in different layouts.
The devices are parametric, in the sense that the pattern can be a function of 
external parameters.
For example, a cross mark device can be a function of the mark size, the width of 
cross arms, etc.

The `Device` class provides a common interface to define parameters and drawing 
functions. To create a new device, simply derive the `Device` class and provide
an implementation for parameters and geometry:
    
    def MyFancyDevice(Device):
        def initialize(self):
            # Initialization stuff goes here
            pass
        def parameters(self):
            # Parameters are defined here
            pass
        def geom(self):
            # Drawing goes here
            pass
        def ports(self):
            # Ports go here
            pass
    
    # To use:
    dev = MyFancyDevice.build()
    geom = dev.run()
        
As bare minimum, the initialize, parameters and geom methods should be re-implemented in a 
device class. 

### Device name
When initializing the device it is very important to give it a unique name as a string
(and optionally a description).
This is done in the `Device.initialize` method:
    
    def initialize(self):
        self.set_name("MYDEVICE")
        self.set_decription("First version of MYDEVICE")
   
The name is used to call devices later on (see Device registraiton below) and 
to instantiate them in circuits.

### Parameters
Device paramters must be defined via the function `Device.add_parameter` as follows:
    
    def parameters(self):
        self.add_parameter("my_param", default_value, "Description", type, (min, max))
        
The default value is usually hard-coded into the device itself and should be the
reference value for creating the geometry. Optionally, the parameter type can be specified
as `bool` or `int` or `float`. The use of string is not recommended but it is not 
forbidden. Also optionally, a range can be specified for integer and float values as a tuple.
This helps the user of the device in figuring out what makes sense. For example:
    
    def parameters(self):
        self.add_parameter("length", 15, "Length of the marker", float, 2, 30)

To use one of the parameter in the drawing, use the `Device.get_params` function
to get a dictionary of the parameters with values:
    
    def geom(self):
        p = self.get_params()
        L = p["length"] # Marker length
    
### Drawing the geometry
The `Device.geom` method should be implemented so that it returns a `samplemaker.shapes.GeomGroup`
object with the geometry. 

The user should never run the `Device.geom` method, but use instead `Device.run` (see example above).

### Building, running, what is all that?
A device object is never instantiated via its constructor __init__ but using
the class method `Device.build`. 
Building a device is like initializing it, setting the default parameters and preparing the device
to be drawn.
To actually draw the geometry you use the `Device.run` method, which ensures that
the exact sequence of operation is carried out. 

### Device registration
To use the re-use the devices later on, it is common practice to build a library of
devices (containing all the classes) and register the devices to a shared dictionary
that other functions can use to build/run named devices.
This is achieved via the `registerDevicesInModule` which can be called at the end
of each python script and will update a hidden device database. 
Building a device is then simply done as

    dev = Device.build_registered("MYDEVICE")
    geom = dev.run()    

See example


Device Ports
------------
An important part of device creation is to define ports that can connect a device
to another one. 
To define ports, `samplemaker` provides the base class `DevicePort`.
The class defines a named port, with position and orientation.

The device ports are specified by re-implementing the `Device.ports` function and
calling the `Device.addport` method:
    
    def ports(self):
        p1 = DevicePort(20,40,True,True)
        self.addport("port1", p1)

The above code generates a `DevicePort` placed at (20,40) facing east.
The two boolean define whether the port is oriented horizontally or vertically
and if it faces forward or backward. 
Check the documentation of `DevicePort` to learn more about port properties.

Quite often, when creating ports, it is necessary to use some variable which is
only defined locally in the geom() function.
To define ports directly from geom(), one can use the method `Device.addlocalport`
instead and leave the ports() methods not implemented:
    
    def geom(self):
        p1 = DevicePort(20,40,True,True)
        self.addlocalport("port1", p1) 
        
Do not use `Device.addport` from the geom() command as it will not work.

### Implementing custom device ports
Users can define different port types by inheriting the `DevicePort` class. 
For example one might be interested in defining optical ports (for waveguide devices)
and electrical ports (for electronic circuits).
The default DevicePort in fact cannot be connected to anything until the user
supplies a connector function.
For example

        
    def OpticalPortConnector(port1: "DevicePort",port2: "DevicePort") -> "GeomGroup":
        # functions that calculate and draw the connector
        return geom

    class OpticalPort(DevicePort):
        def __init__(self,x0,y0,horizontal,forward,width,name):
            super().__init__(x0,y0,horizontal,forward)
            self.width = width
            self.name=name
            self.connector_function=OpticalPortConnector

The newly created OpticalPort can now be connected to other OpticalPort ports.

Circuits
---------
Once ports are specified, it is possible to create circuits that connect various 
devices with each others.
A circuit is itself a `Device` with parameters and ports, except the drawing routine is
controlled by a netlist that defines what devices should be instantiated, where,
and how connectivity is defined.

### Defining a netlist
The `NetList` class speficies a circuit layout. To specify a Netlist, you need to 
provide a list of entries via the class `NetListEntry`. 
A single entry of the netlist correspond to a device name (which should be registered)
position, and connectivity:
    
    entry1 = NetListEntry("MYDEVICE", 0, 0, "E", {"port1":"inA","port2":"inB"}, {"length":16})
    
In the above example MYDEVICE will be placed in 0,0 facing East ("E") and his parameter "length" will be set to 16. 
Additionally the named DevicePort "port1" has been assigned to wire "inA" and "port2" to wire "inB".
The circuit builder will look for any other entry where a port has been assigned to wire "inA" and run
the connector (provided by user) between the two ports.
If a matching port cannot be found, the wire will become the name of an external port of the entire circuit.

The netlist is then built specifying the list of entries and a circuit can be build exactly as a 
standard device:
    
    netlist = NetList("my_circuit", [entry1,entry2,entry3])
    cir_dev = Circuit.build() # Note that we build first
    cir_dev.set_param("NETLIST") = netlist # Set the NETLIST parameter
    g = cir_dev.run() # and finally run the device

More details on specifying circuits are given in the tutorials, where it is also
explained how to nest circuits together (i.e. creating netlists of netslists)


"""

import math
import sys,inspect
import numpy as np
from copy import deepcopy
from samplemaker.shapes import GeomGroup, Poly
from samplemaker.makers import make_sref, make_text
from samplemaker import LayoutPool, _DeviceCountPool, _DeviceLocalParamPool, _DevicePool
from samplemaker.gdswriter import GDSWriter
from samplemaker.gdsreader import GDSReader


class DevicePort: 
    def __init__(self,x0,y0,horizontal,forward):
        self.x0=x0
        self.y0=y0
        self.__px = x0
        self.__py = y0
        self.hv = horizontal
        self.bf = forward
        self.__hv = horizontal
        self.__bf = forward
        self.name = ""
        self._geometry = GeomGroup() # it can carry a full geom to which it is connected
        self._parentports = dict()  # any other port shared with this port in the same device
        self.connector_function = None
    
    def set_name(self,name):
        self.name=name
    
    def angle(self):
        return math.pi*(3-(self.hv+self.bf*2))/2
        
    def set_angle(self,angle):
        i = round(3-angle*2/math.pi)%4
        self.hv = i%2==1
        self.bf = math.floor(i/2)==1
        
    def printangle(self):
        if(self.hv and self.bf): print("E")
        if(self.hv and not self.bf): print("W")
        if(not self.hv and self.bf): print("N")
        if(not self.hv and not self.bf): print("S")
        
    def angle_to_text(self):
        if(self.hv and self.bf): return "E"
        if(self.hv and not self.bf): return "W"
        if(not self.hv and self.bf): return "N"
        if(not self.hv and not self.bf): return "S"
        
    def dx(self):
        return self.hv*(2*self.bf-1)
    def dy(self):
        return (not self.hv)*(2*self.bf-1)
    def rotate(self,x0,y0,angle):
        xc=self.x0-x0
        yc=self.y0-y0
        cost = math.cos(math.radians(angle))
        sint = math.sin(math.radians(angle))
        self.x0=cost*xc-sint*yc+x0
        self.y0=sint*xc+cost*yc+y0
        self.set_angle(self.angle()+math.radians(angle))
        
    def S(self,amount):
        self.x0+=self.dx()*amount
        self.y0+=self.dy()*amount
    def BL(self,radius):
        xc = self.x0-self.dy()*radius
        yc = self.y0+self.dx()*radius
        phi = self.angle()-math.pi/2
        self.x0=radius*math.cos(phi+math.pi/2)+xc
        self.y0=radius*math.sin(phi+math.pi/2)+yc
        self.set_angle(self.angle()+math.pi/2)
    def BR(self,radius):
        xc = self.x0+self.dy()*radius
        yc = self.y0-self.dx()*radius
        phi = self.angle()+math.pi/2
        self.x0=radius*math.cos(phi-math.pi/2)+xc
        self.y0=radius*math.sin(phi-math.pi/2)+yc
        self.set_angle(self.angle()-math.pi/2)
    
    def reset(self):
        self.x0=self.__px
        self.y0=self.__py
        self.hv=self.__hv
        self.bf=self.__bf
        
    def fix(self):
        self.__px=self.x0
        self.__py=self.y0
        self.__hv=self.hv
        self.__bf=self.bf
    
    def dist(self,other):
        dx = other.x0-self.x0
        dy = other.y0-self.y0
        return math.sqrt(dx*dx+dy*dy)


    
class Device:
    def __init__(self):
        """
        Initializes a Device. Should never be called.

        Returns
        -------
        None.

        """
        self._p = dict()
        self._pdescr = dict()
        self._ptype = dict() #stores the type of the parameter
        self._prange = dict() # stores the min-max range of the parameter in a tuple
        self._localp = dict()
        self.addlocalparameter("_ports_", dict(), "Ports calculated by geom")
        self._x0 = 0
        self._y0 = 0
        self._hv = True
        self._bf = True
        self._ports = dict()
        self._name = ""
        self._description = "No description yet"
        self.use_references = True
    
    def __hash__(self):
        return hash((frozenset(self._p.items()), self._name))
    
    def angle(self):
        """
        Returns the orientation of the device in radians.

        Returns
        -------
        float
            The orientation in radians (east = zero).

        """
        return math.pi*(3-(self._hv+self._bf*2))/2
    
    def set_angle(self,angle:float):
        """
        Changes the orientation of the device

        Parameters
        ----------
        angle : float
            The new angle in radians.

        Returns
        -------
        None.

        """
        i = round(3-angle*2/math.pi)%4
        self._hv = i%2==1
        self._bf = math.floor(i/2)==1
        
    def addport(self,port: DevicePort):
        """
        Call this from the ports() method to add a port to the device.

        Parameters
        ----------
        port : DevicePort
            The device port.

        Returns
        -------
        None.

        """
        self._ports[port.name]=port
        
    def addparameter(self, param_name: str, default_value, param_description: str, param_type=float, param_range=(0,np.infty)):
        """
        Call this from the parameters() method to add a parameter to the device.
        
        Parameters
        ----------
        param_name : str
            The name of the parameter.
        default_value : TYPE
            The default value.
        param_description : str
            A text describing the parameters.
        param_type : TYPE, optional
            The type of the parameter. The default is float.
        param_range : tuple, optional
            A tuple specifying the min and max value of the parameter . The default is (0,np.infty).

        Returns
        -------
        None.

        """
        if(param_name.find(":")!=-1):
            print("Cannot define variable names containing ':'")
            return
        self._p[param_name] = default_value
        self._pdescr[param_name] = param_description
        self._ptype[param_name] = param_type
        self._prange[param_name] = param_range
        
    def addlocalparameter(self,param_name: str, default_value, param_description: str, param_type=float, param_range=(0,np.infty)):
        """
        Defines a local parameter that is only used within the class and not 
        controllable from outside. 

        Parameters
        ----------
        param_name : str
            The parameter name.
        default_value : TYPE
            The value of the paramter.
        param_description : str
            Description of the parameter.
        param_type : TYPE, optional
            The type of the paramter. The default is float.
        param_range : tuple, optional
            A tuple specifying the min and max value of the parameter . The default is (0,np.infty).

        Returns
        -------
        None.

        """
        if(param_name.find(":")!=-1):
            print("Cannot define variable names containing ':'")
            return
        self._localp[param_name] = default_value
        self._pdescr[param_name] = param_description    
        self._ptype[param_name] = param_type
        self._prange[param_name] = param_range
        
    def addlocalport(self,port):
        """
        Same as local parameter, but allows creating ports from the geom() function.
        If you need some info from the geom() function to create ports just add
        local ports and they will be automatically added to ports by the port() function.

        Parameters
        ----------
        port : DevicePort
            The port to be added.

        Returns
        -------
        None.

        """
        self._localp["_ports_"][port.name] = port
    
    def set_param(self,param_name: str, value):
        """
        Change a paramter. To be called after build().

        Parameters
        ----------
        param_name : str
            The parameter to be changed.
        value : TYPE
            The new value of the parameter.

        Returns
        -------
        None.

        """
        param_hier = param_name.split("::")
        p = self._p
        for i in range(len(param_hier)):
            if i==(len(param_hier)-1):
                if(param_hier[i] in p):
                    p[param_hier[i]] = value                
                else:
                    print("Could not set parameter named", param_hier[i], "as it was not defined by device.")
                    return
            else:
                if(param_hier[i] in p):
                    p = p[param_hier[i]]                
                else:
                    print("Could not set parameter named", param_hier[i], "as it was not defined by device.")
                    return

    def get_params(self, cast_types:bool = True, clip_in_range:bool = True) ->dict :
        """
        To be called by geom() functions. Returns the dictionary with all parameters.

        Parameters
        ----------
        cast_types : bool, optional
            Attempts to do a type-cast on the parameter. The default is True.
        clip_in_range : bool, optional
            Clips the value in the range specified. The default is True.

        Returns
        -------
        dict
            A dictionary with the parameter value map.

        """
        if cast_types:
            for p,val in self._p.items():
                val=self._ptype[p](val)
        if clip_in_range:
            for p,val in self._p.items():
                if val<self._prange[p][0]:
                    val = self._prange[p][0]
                if val>self._prange[p][1]:
                    val = self._prange[p][1]
        return self._p

    def get_port(self,port_name: str):
        """
        Should not be called by user. Returns the named port.

        Parameters
        ----------
        port_name : str
            Name of the port.

        Returns
        -------
        DevicePort
            The DevicePort object associated to the port (empty if does not exist).

        """
        if(port_name in self._ports):
            return self._ports[port_name]
        else:
            print("Could not find port named", port_name, "in",self._name, "as it was not defined by device.")
            return DevicePort()
        
    def set_name(self, name: str):
        """
        Sets the device name (should be called from initialize).

        Parameters
        ----------
        name : str
            The device name.

        Returns
        -------
        None.

        """
        self._name = name
    
    def set_description(self, descr: str):
        """
        Sets the device description (should be called from initialize)

        Parameters
        ----------
        descr : str
            the device description.

        Returns
        -------
        None.

        """
    
    def initialize(self):
        """
        Re-implement this function in your device to initialize and set the device name

        Returns
        -------
        None.

        """
        pass
    
    def parameters(self):
        """
        Re-implement this function to define parameters of the device

        Returns
        -------
        None.

        """
        pass
    
    def geom(self):
        """
        Re-implement this function to generate the geometry of the device.

        Returns
        -------
        None.

        """
        pass
        
    def run(self):
        """
        Runs the device and generates a geometry.

        Returns
        -------
        g : samplemaker.shapes.GeomGroup
            The geometry of the device.

        """
        if(self.use_references):
            # Check if it is in the device pool
            hsh = self.__hash__()
            if "NETLIST" in self._p:
                srefname = self._p["NETLIST"].name         
            else:
                srefname = self._name
            if srefname not in _DeviceCountPool:
                _DeviceCountPool[srefname]=0
            
            if hsh not in _DevicePool:
                _DeviceCountPool[srefname] += 1
                srefname += "_%0.4i"%_DeviceCountPool[srefname]
                LayoutPool[srefname] = self.geom()
                _DevicePool[hsh] = srefname
                _DeviceLocalParamPool[hsh] = deepcopy(self._localp)
            else:
                srefname += "_%0.4i"%_DeviceCountPool[srefname]
                self._localp = _DeviceLocalParamPool[hsh]
            # now create a ref
            g = make_sref(self._x0,self._y0, _DevicePool[hsh], 
                          LayoutPool[_DevicePool[hsh]],
                          angle=math.degrees(self.angle()))  
        else:
            g = self.geom()
            g.rotate_translate(self._x0,self._y0,math.degrees(self.angle()))
            #g.rotate(0,0,math.degrees(self.angle()))
            #g.translate(self._x0,self._y0)

        self.ports() # this will get the proper local parameters as if self.geom() ran properly
        # Now rotate/translate all ports
        for port in self._ports.values():
            port.rotate(0,0,math.degrees(self.angle()))
            port.x0 += self._x0
            port.y0 += self._y0
        return g
    
    def ports(self):
        """
        Re-implement this to define ports.
        If localports are used via the geom() function do not re-implement.

        Returns
        -------
        None.

        """
        if("_ports_" in self._localp.keys()):
            for p in self._localp["_ports_"].values():
                self.addport(deepcopy(p))
        pass
        
    @staticmethod
    def build_registered(name: str):
        """
        Builds a device from the pool of registered device names.

        Parameters
        ----------
        name : str
            The device name to be built.

        Returns
        -------
        Device
            The device to be built.

        """
        if(name in _DeviceList):
            return _DeviceList[name].build()
        else:
            print("No device named",name,"found.")
    
    @classmethod
    def build(cls):
        """
        Class method to build a device.

        Parameters
        ----------
        cls : Device
            The Device class.

        Returns
        -------
        device : Device
            Instance of the Device ready to be rendered via the run() method.

        """
        device = cls()
        device.initialize()
        device.parameters()
        device.ports()
        return device


class NetListEntry:
    def __init__(self,devname: str, x0: float, y0: float, rot: str, 
                 portmap: dict, params: dict):
        """
        Defines a single entry in a NetList.

        Parameters
        ----------
        devname : str
            The registered device name.
        x0 : float
            x coordinate of the device.
        y0 : float
            y coordinate of the device.
        rot : str
            String that defines the orientation of the device (can only be "N", "S", "W" or "E").
        portmap : dict
            A dictionary that associates a port in the device to a wire.
        params : dict
            A dictionary of parameters to be used when creating the device.

        Returns
        -------
        None.

        """
        self.devname = devname
        self.x0 = x0
        self.y0 = y0
        self.rot= 0
        if (rot=="N"):
            self.rot = 90
        if(rot=="W"):
            self.rot = 180
        if(rot=="S"):
            self.rot = 270
        self.portmap = portmap
        self.params = params
        
    def __hash__(self):
        return hash((self.devname,self.x0,self.y0,self.rot,frozenset(self.portmap.items()),frozenset(self.params.items())))
                

class NetList:
    def __init__(self,name,entry_list):
        """
        Creates a new NetList for circuit generation.

        Parameters
        ----------
        name : str
            The netlist name.
        entry_list : list
            list of `NetLisEntry` objects.

        Returns
        -------
        None.

        """
        self.name = name
        self.entry_list = entry_list
        self.external_ports = []
        self.aligned_ports = []
    
    def __hash__(self):
        return hash((self.name,tuple(self.entry_list),tuple(self.external_ports),
                     tuple(self.aligned_ports)))
    
    def set_external_ports(self, ext_ports: list):
        """
        Define a list of wires (list of strings) that should be 
        connected outside the circuit.

        Parameters
        ----------
        ext_ports : list
            A list of strings with the wires assigned to ports in the netlist entry.

        Returns
        -------
        None.

        """
        self.external_ports = ext_ports
        
    def set_aligned_ports(self, aligned_ports: list):
        """
        Define a list of wires (list of strings) that should be
        aligned with each other

        Parameters
        ----------
        aligned_ports : list
             A list of strings with the wires assigned to ports in the netlist entry.

        Returns
        -------
        None.

        """
        self.aligned_ports = aligned_ports
        
    @classmethod
    def ImportCircuit(cls, file_name: str, circuit_name: str):
        """
        Generates a NetList object from a circuit file.
        The input is a text file with circuit description similar to the
        SPICE netlist format (yet with some important differences). 
        Check the tutorials for examples.

        Parameters
        ----------
        cls : NetList
            NetList class.
        file_name : str
            The circuit filename.
        circuit_name : str
            The subcircuit to load inside the circuit file.

        Returns
        -------
        NetList
            The NetList with the imported circuit.

        """
        # Import all netlists
        with open(file_name) as f:
            current_netlist = ""
            current_entrylist = []
            current_align = []
            all_lists = dict(); # stores all the imported netlists
            for line in f:
                tokens = line.split()
                if(len(tokens)==0): # empty line
                    continue 
                if(tokens[0][0]=="#"): #Comment
                    continue 
                if(tokens[0]==".CIRCUIT" and current_netlist == ""):
                    current_netlist =  tokens[1:]
                    print("Reading ", current_netlist[0])
                    continue
                if(tokens[0]==".ALIGN" and current_netlist != ""):
                    current_align = tokens[1:]
                    continue
                if(tokens[0]==".END" and current_netlist != ""):
                    clist = cls(current_netlist[0],deepcopy(current_entrylist))
                    clist.aligned_ports=current_align;
                    clist.external_ports=current_netlist[1:]
                    current_entrylist = []
                    current_netlist = ""
                    current_align = []
                    all_lists[clist.name]=clist
                    continue
                # Now we should have only entries
                if(current_netlist!=""):
                    # parse entries
                    devname=tokens[0]
                    params = dict();
                    cin = 1
                    if(devname=="X"):
                        params["NETLIST"] = all_lists[tokens[1]] # must exist
                        cin+=1
                    x = float(tokens[cin]); cin+=1
                    y = float(tokens[cin]); cin+=1
                    rot = tokens[cin]; cin+=1
                    portdict = dict()
                    while tokens[cin]!=".": # Should always end the entry with a dot 
                        portdict[tokens[cin]]=tokens[cin+1]
                        cin+=2
                    cin+=1
                    while cin<len(tokens):
                        params[tokens[cin]]=float(tokens[cin+1])
                        cin+=2
                    current_entrylist.append(NetListEntry(devname, x, y, rot, portdict, params))
                    
                    
        return all_lists[circuit_name]
        
    
class Circuit(Device):
    
    def __flatdict(self,d,parent_str):
        flatdict=dict()
        for key,value in d.items():
            if type(value)==dict:
                newdict = self.__flatdict(value,parent_str+key+"::")
                for key,value in newdict.items():
                    flatdict[key]=value
            else:
                flatdict[parent_str+key]=value
        return flatdict
    
    def __hash__(self):
        flatdict = self.__flatdict(self._p,"")
        return hash((frozenset(flatdict.items()), self._name))
    
    def initialize(self):
        """
        Names the Circuit as 'X' to be referred in other circuits

        Returns
        -------
        None.

        """
        self._name = "X"
        pass
    
    def parameters(self):
        """
        Defines the parameter NETLIST taking a `NetList` object as input.

        Returns
        -------
        None.

        """
        self.addparameter("NETLIST", [],"A list of NetListEntry specifying a circuit")
        self.addlocalparameter("external_ports", dict(), "Locally store the ports that connect to the circuit")
        pass
    
    def update_parameters(self):
        netlist = self._p["NETLIST"].entry_list;
        i = 1
        for nle in netlist:
            if nle.devname not in _DeviceList:
                print("Warning, no device named",nle.devname,"found.")
            else:
                dev=_DeviceList[nle.devname].build()
                for key,value in nle.params.items():
                    dev.set_param(key,value)
                self.addparameter("dev_%s_%i"%(nle.devname,i), dev._p, "Device parameters for %s"%nle.devname)
            i+=1
           
    def set_param(self, param_name: str, value):
        """
        Sets the value of a parameter. In a Circuit, you can refer to 
        individual device parameters by using the following convention:
        
            dev.set_param("dev_MYDEVICE_1::length", 12)
            
        which sets parameter "length" of the first instance of MYDEVICE to 12.
        The format is "dev_%devicename_%number", where %devicename is the registered
        device name and %number is the device entrylist number (starting from 1).

        Parameters
        ----------
        param_name : str
            Parameter name.
        value : 
            Value.

        Returns
        -------
        None.

        """
        super().set_param(param_name, value)
        if(param_name=="NETLIST"):
            self.update_parameters()
                     
    
    def geom(self):
        """
        Draws the entire circuit.

        Returns
        -------
        g : samplemaker.shapes.GeomGroup
            The entire circuit geometry including connectors.

        """
        netlist = self._p["NETLIST"].entry_list
        external_ports = self._p["NETLIST"].external_ports
        aligned_ports = self._p["NETLIST"].aligned_ports
        input_ports = dict()
        output_ports = dict()
        # Instantiate all devices
        g = GeomGroup();
        i = 1
        for nle in netlist:
            if nle.devname not in _DeviceList:
                print("Warning, no device named",nle.devname,"found.")
                return g
            dev=_DeviceList[nle.devname].build()
            dev.use_references = self.use_references
            # Set all parameter from Netlist hierarchy
            dev._p = self._p["dev_%s_%i"%(nle.devname,i)]
            i+=1
            dev._x0 = nle.x0
            dev._y0 = nle.y0
            dev.set_angle(math.radians(nle.rot))
            geom = dev.run()
            g+=geom
            for devport,conn_name in nle.portmap.items():
                port = dev.get_port(devport)
                port._geometry = geom
                port._parentports = dev._ports
                if conn_name in input_ports:
                    output_ports[conn_name] = port
                else:
                    input_ports[conn_name] = port

        # Now we align ports
        for portname in aligned_ports:
            if portname in input_ports.keys() and portname in output_ports.keys():
                # port 2 is always slave to port1 
                port1 = input_ports[portname]
                port2 = output_ports[portname]
                if(port1.dx() != 0 and port2.dx() != 0):
                    # align y-values
                    ydiff = port2.y0-port1.y0
                    port2._geometry.translate(0,-ydiff)
                    for pp in port2._parentports.values():
                        pp.y0 -= ydiff
                if(port1.dy() != 0 and port2.dy() != 0):
                    # align x values
                    xdiff = port2.x0-port1.x0
                    port2._geometry.translate(-xdiff,0)
                    for pp in port2._parentports.values():
                        pp.x0 -= xdiff
                    
                
        # Now we run connectors
        for portname in input_ports.keys():
            port1 = input_ports[portname]
            if portname in output_ports:
                port2 = output_ports[portname]
                if(port1.connector_function == port2.connector_function):
                    g+=port1.connector_function(port1,port2)
                else:
                    print("Warning, incompatible ports for connection named",portname)
            else:
                if portname in external_ports:
                    port1._geometry = GeomGroup()
                    port1._parentports = dict()
                    p1 = deepcopy(port1)
                    p1.name=portname
                    self._localp["external_ports"][portname]=p1
                else: 
                    print("Warning: port",portname,"is unconnected")
        return g
    
    def ports(self):
        """
        Adds external ports that are not connected in the netlist.

        Returns
        -------
        None.

        """
        ext_ports = self._localp["external_ports"]
        for p in ext_ports.values():
            self.addport(deepcopy(p))

# class DeviceTableAnnotations:
#     def __init__(self,colfmt, rowfmt, xoff, yoff, colvars, rowvars,
#                  text_width=5, text_height=5,
#                  left = True,right =True,above = True,below = True):
#         self.colfmt = colfmt
#         self.rowfmt = rowfmt
#         self.colvars = colvars
#         self.rowvars = rowvars
#         self.left = left
#         self.right = right
#         self.above = above
#         self.below = below
#         self.xoff = xoff
#         self.yoff = yoff
#         self.text_width = text_width
#         self.text_height = text_height
#         #possible formats are
#         # headers
#         # headersR
#         # headersL
#         # side
    
#     def render(self,i,j,cols,rows,x0,y0,coldict, rowdict):
#         coltxt = deepcopy(self.colfmt)
#         rowtxt = deepcopy(self.rowfmt)
#         coltxt = coltxt.replace("%I",str(i))
#         rowtxt = rowtxt.replace("%I",str(i))
#         coltxt = coltxt.replace("%J",str(j))
#         rowtxt = rowtxt.replace("%J",str(j))
#         for v in range(len(self.colvars)):
#             pstr = "%C"+str(v)
#             coltxt = coltxt.replace(pstr,str(coldict[self.colvars[v]][i]))
#             rowtxt = rowtxt.replace(pstr,str(coldict[self.colvars[v]][i]))
#         for v in range(len(self.rowvars)):
#             pstr = "%R"+str(v)
#             coltxt = coltxt.replace(pstr,str(rowdict[self.rowvars[v]][j]))
#             rowtxt = rowtxt.replace(pstr,str(rowdict[self.rowvars[v]][j]))  
#         g = GeomGroup();
#         if(self.left and i==0):
#             x = x0-self.xoff
#             y = y0
#             g+= make_text(x,y,rowtxt,self.text_width,self.text_height)
#         if(self.right and i==(cols-1)):
#             x = x0+self.xoff
#             y = y0
#             g+= make_text(x,y,rowtxt,self.text_width,self.text_height)
#         if(self.above and j==(rows-1)):
#             x = x0
#             y = y0+self.yoff
#             g+= make_text(x,y,coltxt,self.text_width,self.text_height)
#         if(self.below and j==0):
#             x = x0
#             y = y0-self.yoff
#             g+= make_text(x,y,coltxt,self.text_width,self.text_height)
        
#         return g
    

# class DeviceTable(Device):
#     def __flatdict(self,d,parent_str):
#         flatdict=dict()
#         for key,value in d.items():
#             if type(value)==dict:
#                 newdict = self.__flatdict(value,parent_str+key+"::")
#                 for key,value in newdict.items():
#                     flatdict[key]=value
#             elif type(value)==np.ndarray:
#                 flatdict[parent_str+key]=value.tostring()
#             else:
#                 flatdict[parent_str+key]=value
#         #print(flatdict, " from ", parent_str)
#         return flatdict
    
#     def __hash__(self):
#         flatdict = self.__flatdict(self._p,"")
#         return hash((frozenset(flatdict.items()), self._name))
    
#     @staticmethod
#     def Regular(cols:int,rows:int,ax:float,ay:float,bx:float,by:float):
#         return tuple([tuple([(i*ax+j*bx,i*ay+j*by) for i in range(cols)]) for j in range(rows)])
       
#     # @staticmethod
#     # def WriteField(cols:int,rows:int,ax:float,ay:float,bx:float,by:float,
#     #                       wfsize: float, wfx: float, wfy: float, dev_bb: List[float],wfdist: float = 20):
#     #     for i in range(cols):
#     #         for j in range(rows):
#     #             xc = i*ax+j*ay
#     #             yc = i*bx+j*by
#     #             if xc
        
#     #     return tuple([tuple([(i*ax+j*ay,i*bx+j*by) for i in range(cols)]) for j in range(rows)])
    
#     def initialize(self):
#         self._name = "TABLE"
#         pass
    
#     def parameters(self):
#         self.addparameter("columns", 1,"Number of columns",int)
#         self.addparameter("rows", 1,"Nomber of rows",int)
#         self.addparameter("table_positions",(((0,0),),),"A colsxrows tuple of coordinates for placing the elements")
#         self.addparameter("default_params", dict(), "A dictionary of default parameter to be assigned before device creation")
#         self.addparameter("col_variables", dict(),"A list of variables and values to be changed along columns")
#         self.addparameter("row_variables", dict(),"A list of variables and values to be changed along rows")
#         self.addparameter("device_name", "", "A device to be used in a table",str)
#         self.addparameter("device_rot",0,"Device rotation",float)
#         self.addparameter("col_linkports", (), "Tuple of tuples containing port names that should be linked along columns")
#         self.addparameter("row_linkports", (), "Tuple of tuples containing port names that should be linked along rows")
#         self.addparameter("col_alignports", False, "The first pair specified in col_linkports will be aligned",bool)
#         self.addparameter("row_alignports", False, "The first pair specified in col_linkports will be aligned",bool)
#         self.addparameter("annotations",DeviceTableAnnotations("","",0,0,(),()),"The device annotations")
#         self.addlocalparameter("external_ports", dict(), "Locally store the ports that connect to the circuit")
        
#     def geom(self):
#         devname = self._p["device_name"]
#         default_params = self._p["default_params"]
#         if devname not in _DeviceList:
#             print("Warning, no device named",devname,"found.")
#             return GeomGroup()
#         g = GeomGroup();
#         dev = _DeviceList[devname].build()
#         for key,value in default_params.items():
#             dev.set_param(key,value)
#         cols = self._p["columns"]
#         rows = self._p["rows"]
#         pos_xy = self._p["table_positions"]

#         cvars = self._p["col_variables"]
#         rvars = self._p["row_variables"]
        
#         clports = self._p["col_linkports"]
#         rlports = self._p["row_linkports"]
        
#         clalign = self._p["col_alignports"]
#         rlalign = self._p["row_alignports"]
        
#         dta = self._p["annotations"]
        
#         portmap = [[dict() for i in range(cols)] for j in range(rows)] 
#         for i in range(cols):
#             for var,valuelist in cvars.items():
#                 if(len(valuelist)!=cols):
#                     dev.set_param(var,valuelist[0])
#                 else:
#                     dev.set_param(var,valuelist[i])   
#             for j in range(rows):
#                 for var,valuelist in rvars.items():
#                     if(len(valuelist)!=rows):
#                         dev.set_param(var,valuelist[0])
#                     else:
#                         dev.set_param(var,valuelist[j])

#                 dev.set_angle(math.radians(self._p["device_rot"]))
#                 dev._x0 = pos_xy[j][i][0]
#                 dev._y0 = pos_xy[j][i][1]
#                 # ok now we can instantiate
#                 dev.use_references = self.use_references
#                 geom=dev.run()
#                 g+=geom
#                 portmap[j][i] = deepcopy(dev._ports)
#                 # annotations
#                 g+=dta.render(i,j,cols,rows,dev._x0,dev._y0,cvars, rvars)
                
#                 # Column linking
                
#                 if (i>0):
#                     for links in clports:                        
#                         if links[0] in portmap[j][i-1] and links[1] in portmap[j][i]:
#                             p1 = portmap[j][i-1][links[0]]
#                             p2 = portmap[j][i][links[1]]
#                             #print(i,j,p1.x0,p1.y0,p2.x0,p2.y0)
#                             if(p1.connector_function == p2.connector_function):
#                                 if(clalign and p1.dx() != 0 and p2.dx() != 0):
#                                     ydiff = p2.y0-p1.y0
#                                     geom.translate(0,-ydiff)
#                                     for pp in portmap[j][i].values():
#                                         pp.y0 -= ydiff    
                                                                        
#                                 g+=p1.connector_function(p1,p2)                                
#                             else:
#                                 print("Warning, incompatible ports for connection between",p1.name,
#                                       "and",p2.name)              
#                 if (j>0):
#                     for links in rlports:  
#                         if links[0] in portmap[j-1][i] and links[1] in portmap[j][i]:
#                             p1 = portmap[j-1][i][links[0]]
#                             p2 = portmap[j][i][links[1]]
#                             #print(i,j,p1.x0,p1.y0,p2.x0,p2.y0)
#                             if(p1.connector_function == p2.connector_function):
#                                 if(rlalign and p1.dy() != 0 and p2.yx() != 0):
#                                     xdiff = p2.x0-p1.x0
#                                     geom.translate(0,-xdiff)
#                                     for pp in portmap[j][i].values():
#                                         pp.x0 -= xdiff    
#                                 g+=p1.connector_function(p1,p2)
#                             else:
#                                 print("Warning, incompatible ports for connection between",p1.name,
#                                       "and",p2.name)             
        
#                 # Store external ports to expose them
#                 for pp in portmap[j][i].values():
#                     p1 = deepcopy(pp)
#                     p1.name+="_%i_%i"%(i,j)
#                     self._localp["external_ports"][p1.name]=p1
#         return g
    
#     def ports(self):
#         ext_ports = self._localp["external_ports"]
#         for p in ext_ports.values():
#             self.addport(deepcopy(p))


_DeviceList = dict()
_DeviceList["X"]=Circuit
#_DeviceList["TABLE"]=DeviceTable


def registerDevicesInModule(module_name: str):
    """
    To be called at the end of a python module containing device classes 
    that inherit the `Device` class. It will register the device names in a
    global database.

    Parameters
    ----------
    module_name : str
        The python module name, if used in the same file, just use `__name__`.

    Returns
    -------
    None.

    """
    for name, obj in inspect.getmembers(sys.modules[module_name]):
        if inspect.isclass(obj):
            #print("found",name)
            # Recursively check bases for Device
            baseobj = obj.__bases__[0];
            while(baseobj!=Device):
                if len(baseobj.__bases__)!=0:
                    baseobj = baseobj.__bases__[0]
                else: break
                
            if(baseobj==Device):
                oj = obj()
                oj.initialize()
                _DeviceList[oj._name] = obj
                print("found",oj._name)

def CreateDeviceLibrary(devname: str, params: dict, filename: str):
    """
    Generates a GDS file with a re-usable GDS-format device.
    Also exports ports as text element in GDS.
    Flattens everything

    Parameters
    ----------
    devname : str
        The registered name of the device.
    params : dict
        The parameters to be used when saving. Modifies the default.
    filename: str
        The output library filename

    Returns
    -------
    None.

    """
    dev = Device.build_registered(devname)
    for key,value in params.items():
         dev.set_param(key,value)
    geomE = dev.run()
    for p,val in dev._ports.items():
        idtxt = '__PORT__ ' + p + ' ' + val.angle_to_text() + ' ' + val.__class__.__module__+' '+val.__class__.__name__
        geomE += make_text(val.x0,val.y0,idtxt,0,0)
        
    geomE=geomE.flatten()
    
    
    gdsw = GDSWriter()
    gdsw.open_library(filename)
    gdsw.write_structure(devname, geomE)
    gdsw.close_library()
    

def ExportDeviceSchematics(filename: str = "SampleMakerLibrary.lel"):
    """
    Generates a Layout Editor library file (LEL) containing the Devices currently
    loaded on the Device List. The library file can be used in combination with
    Layout Editor Schematic to produce spice netlists for circuit design.
    
    Parameters
    ----------
    filename : str, optional
        The library filename with .lel extension. The default is "SampleMakerLibrary.lel".

    Returns
    -------
    None.

    """
    f = open(filename,'w')
    for devobj in _DeviceList.values():
        oj = devobj()
        oj.initialize();
        oj.parameters();
        oj.ports();        
        if (oj._name == "X") or (oj._name == "TABLE"):
            continue

        f.write("<Component " + devobj.__name__ + ">\n")
        f.write("<Description>\n" + oj._description + "\n</Description>\n")
        f.write("<Parameter>\n")
        for p,val in oj._p.items():
            valstring = " ".join(map(str,[val]))
            valstring = valstring.replace("<","-").replace(">","-")
            f.write("<string "+p+" " + valstring + ">\n")
        f.write("</Parameter>\n")
        f.write("<Prefix " + oj._name + ">\n")
        #f.write("<Label>\n$devicename\n</Label>\n")
        
        f.write("<Symbol>\n")
        dev = oj.build()
        geomE = dev.run()
        geomE = geomE.flatten()
        bb = geomE.bounding_box()
        scale =1
        #scale = bb.width
        #if bb.height>bb.width:
        #    scale = bb.height
        geomE.scale(0,0,100/scale,100/scale)
        
        for g in geomE.group:
            if type(g)==Poly:
                bb = g.bounding_box()
                if bb.width<2 and bb.height<0.2:
                    continue
                x = g.data[0::2]
                y = g.data[1::2]
                for i in range(len(x)-1):
                    if ((x[i+1]-x[i])**2 +(y[i+1]-y[i])**2 > 0.2): 
                        f.write("<Line {x0} {y0} {x1} {y1} wire>\n".format(x0=int(x[i]),y0=int(y[i]),x1=int(x[i+1]),y1=int(y[i+1])))
                    
        dev.ports()
        for pname, port in dev._ports.items():
            f.write("<Port {x} {y} {name}>\n".format(x=int(port.x0*100/scale),y=int(port.y0*100/scale),name=pname))
            
        f.write("</Symbol>\n")
        #f.write("<Offsetlabel 0 -50 -50>\n")
        f.write("<Netlist spice>\n")
        f.write("$devicename ")
        for pname, port in dev._ports.items():
            f.write("{name} $node({name}) ".format(name=pname))
        f.write(". ")
        for p,val in oj._p.items():
            f.write(p+" $" + p +" ")
        
        f.write("\n</Netlist>\n")
        
        f.write("</Component>\n")
    
    f.close()
    
# The function below is work in progress

# def createDeviceDocumentation(filename: str = "Devices.xml"):
#     f = open(filename,'w')

#     header= """<?xml version="1.0" encoding="UTF-8"?>
#     <samplemaker_devices>"""
#     footer = """</samplemaker_devices>"""
#     f.write(header)

#     for devobj in _DeviceList.values():
#         f.write("<device>\n")
#         oj = devobj()
#         oj.initialize();
#         oj.parameters();
#         oj.ports();
#         f.write("<name>" + oj._name + "</name>\n")
#         f.write("<description>" + oj._description + "</description>\n")
#         f.write("<parameters>\n")
#         for p,val in oj._p.items():
#             f.write("<param>\n")
#             f.write("<pname>"+p+"</pname>\n")
#             valstring = " ".join(map(str,[val]))
#             valstring = valstring.replace("<","-").replace(">","-")
#             f.write("<def_value>"+valstring+"</def_value>\n")
#             f.write("<pdescr>"+oj._pdescr[p]+"</pdescr>\n")
#             f.write("</param>\n")
#         f.write("</parameters>\n")
#         f.write("<ports>\n")
#         if(oj._name != "X" and oj._name != "TABLE"):
#             g = oj.geom()
#             oj.ports()
#             for pname, port in oj._ports.items():
#                 f.write("<port>\n")
#                 f.write("<portname>"+ pname + "</portname>\n")
#                 f.write("<facing>"+ port.angle_to_text() + "</facing>\n")
#                 f.write("<x0>"+ str(port.x0) + "</x0>\n")
#                 f.write("<y0>"+ str(port.y0) + "</y0>\n")
#                 f.write("</port>\n")            
        
#         f.write("</ports>\n")
        
#         f.write("</device>\n")


#     f.write(footer)
        
#     f.close()
        
        
        
        