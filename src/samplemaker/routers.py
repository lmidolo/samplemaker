"""
Automatic port-to-port routing functions.


"""

import math
import numpy as np
from samplemaker.devices import DevicePort
import samplemaker.makers as sm
from copy import deepcopy

# The following are routines for the connector
def __connectable_facing(port1: "DevicePort",port2: "DevicePort",
                       rad: float = 3):
    """
    This function returns true and a sequence 
    if two ports are directly connectable and facing
    each other. The sequence is either a straight line
    or a cosine bend 

    Parameters
    ----------
    port1 : "DevicePort"
        Start port for the connection.
    port2 : "DevicePort"
        End port for the connection.
    rad : float, optional
        The maximum bend radius in um. The default is 3.

    Returns
    -------
    bool
        True if connection succeded, False otherwise.
    list
        A sequence to perform the connection.

    """
    
    # Get the vector from port 1 to port 2
    dx = port2.x0-port1.x0
    dy = port2.y0-port1.y0
    if(port1.dx()!=0):
        # Case1: port 1 is horizontal
        if(abs(dy)<2*rad):
            # the y offset is small enough to use a C bend
            dxsign = 1
            if(abs(dx)!=0): # Note: sometimes this can be zero
                dxsign = dx/abs(dx)
            if(port1.dx()+port2.dx()==0 and dxsign==port1.dx()):
                # facing each other checks
                if(abs(dy)<1e-3):
                    # will use straight line
                    return True,[["S",abs(dx)]]
                else:
                    # will create a C bend
                    slen = (abs(dx)-2*rad)/2
                    if(slen<0):
                        return True,[["C",port1.dx()*dy,abs(dx)/2]]
                    else:
                        return True,[["S",slen],["C",port1.dx()*dy,rad],["S",slen]]
        return False, []
    else: #Case2 : port 1 is vertical
        if(abs(dx)<2*rad):
            # the y offset is small enough to use a C bend
            dysign = 1
            if(abs(dy)!=0):
                dysign = dy/abs(dy)
            if(port1.dy()+port2.dy()==0 and dysign==port1.dy()):
                # facing each other checks
                if(abs(dx)<1e-3):
                    # will use straight line
                    return True,[["S",abs(dy)]]
                else:
                    # will create a C bend
                    slen = (abs(dy)-2*rad)/2
                    if(slen<0):
                        return True,[["C",-port1.dy()*dx,abs(dy)/2]]
                    else:
                        return True,[["S",slen],["C",-port1.dy()*dx,rad],["S",slen]]
        return False, []

def __connectable_bend(port1: "DevicePort",port2: "DevicePort",
                     rad: float = 3):
    """
    This function calculates if two ports can be connected with a single bend
    It calculates the projected intersection of two straight paths and returns
    a sequence that connects the ports. It might sometimes fail if ports are
    too close

    Parameters
    ----------
    port1 : "DevicePort"
        Start port for the connection.
    port2 : "DevicePort"
        End port for the connection.
    rad : float, optional
        The maximum bend radius in um. The default is 3.

    Returns
    -------
    bool
        True if connection succeded, False otherwise.
    list
        A sequence to perform the connection.

    """
    dx1 = port1.dx()
    dx2 = port2.dx()
    dy1 = port1.dy()
    dy2 = port2.dy()
    det = -dx1*dy2+dx2*dy1
    if(det == 0):
        return False, []
    dx = port2.x0-port1.x0
    dy = port2.y0-port1.y0
    t = (-(dx)*dy2+dy*dx2)/det
    s = (-(dx)*dy1+dy*dx1)/det
    if(t>0 and s>0):
        xstp = (t-rad)*port1.dx()
        ystp = (t-rad)*port1.dy()
        s1 = math.sqrt(xstp*xstp+ystp*ystp)
        #xstp = (s-rad)*port2.dx()
        #ystp = (s-rad)*port2.dy()
        #s2 = math.sqrt(xstp*xstp+ystp*ystp)
        p1 = deepcopy(port1)
        p1.S(s1)
        if(det>0): 
            p1.BL(rad)
        else:
            p1.BR(rad)
        res=__connectable_facing(p1, port2,rad)
        seq = [['S',s1],['B',det*90,rad]]+res[1]   
        return True, seq
    else:
        return False, []

def __connect_step(port1: "DevicePort",port2: "DevicePort",
                     rad: float = 3):
    """
    Performs a single connection step, attempts at getting port1 closer to 
    port2 by bending left or right or going straight. This connector works
    well for optical waveguides

    Parameters
    ----------
    port1 : "DevicePort"
        Start port for the connection.
    port2 : "DevicePort"
        End port for the connection.
    rad : float, optional
        The maximum bend radius in um. The default is 3.

    Returns
    -------
    bool
        True if connection succeded, False otherwise.
    list
        A sequence to perform the connection.

    """
    
    seq = []
    if(port1.dx() !=0):
        if(abs(port2.y0-port1.y0)<2*rad): # It's better to bend if too close
            SLen=-1
        else:
            SLen = port1.dx()*(port2.x0+port2.dx()*rad-port1.x0)-rad
        #print("slen in x",SLen)
        if(port2.dx()==0):
            if(abs(port2.x0-port1.x0)<4*rad):
                SLen+=2*rad
            else:
                SLen-=2*rad    
    else:
        if(abs(port2.x0-port1.x0)<2*rad): # It's better to bend if too close
            SLen=-1
        else:
            SLen = port1.dy()*(port2.y0+port2.dy()*rad-port1.y0)-rad
        #print("slen in y",SLen)
        if(port2.dy()==0):
            if(abs(port2.y0-port1.y0)<4*rad):
                SLen+=2*rad
            else:
                SLen-=2*rad    

    if(SLen>0):
        #print("Guessing I should move S by ", SLen)    
        port1.S(SLen)    
        seq = [["S",SLen]]
    # Now see if we get closer by going left or right
    p1 = deepcopy(port1)
    p1.fix()
    p1.BL(rad)
    dL = p1.dist(port2)
    res = __connectable_bend(p1,port2,rad)
    if(res[0]):
        seq += [["B",90,rad]]+res[1]
        return True,seq    
    
    p1.reset()
    p1.BR(rad)
    dR = p1.dist(port2)
    res = __connectable_bend(p1,port2,rad)
    if(res[0]):
        seq += [["B",-90,rad]]+res[1]
        return True,seq

    
    #print("L distance is ", dL)
    #print("R distance is ", dR)
    # Should I go left or right?
    if(dL<dR):
        port1.BL(rad)
        port1.fix()
        return False,(seq+[["B",90,rad]])
    else:
        port1.BR(rad)
        port1.fix()
        return False,(seq+[["B",-90,rad]])
            

def WaveguideConnect(port1: "DevicePort",port2: "DevicePort",
                     rad: float = 3):
    """
    Simple waveguide connector for two ports. Given a start port and an
    end port, the function attempts to connect the ports using 
    a sequence of straight lines (sequencer command S), 90 degrees bends 
    (sequencer command B) and cosine bends (sequencer command C).
    The bending radius is also given. If the ports are too close 
    to be connected via Manhattan-style connectors the function returns
    False.
    The sequence can be used in combination with any 
    `samplemaker.sequencer.Sequencer` class that implements the commands
    S, C, and B. 

    Parameters
    ----------
    port1 : "DevicePort"
        Start port for the connection.
    port2 : "DevicePort"
        End port for the connection.
    rad : float, optional
        The maximum bend radius in um. The default is 3.

    Returns
    -------
    bool
        True if connection succeded, False otherwise.
    list
        A sequence that realizes the connection.


    """
    # Trivial cases first
    res = __connectable_facing(port1, port2,rad)
    if(res[0]):
        #print("connectable facing")
        return True,res[1]
    res = __connectable_bend(port1,port2,rad);
    if(res[0]):
        #print("connectable")
        return True,res[1]
    else:
        p1 = deepcopy(port1)
        seq = []
        for i in range(4):
            res = __connect_step(p1, port2,rad)
            seq += res[1]
            if(res[0]): break
        if(i<4):
            return True,seq
         
    return False,[]

def ElbowRouter(port1: "DevicePort",port2: "DevicePort", offset: float = 5): 
    """
    Simple elbow connector based on Bezier curve, typically used for electrical interconnects.
    Does not check collisions. 
    The offset parameter controls how far should the connector go straight out 
    of the ports before attempting a connection (using cubic Bezier).

    Parameters
    ----------
    port1 : "DevicePort"
        Start port for the connection.
    port2 : "DevicePort"
        End port for the connection.
    offset : float, optional
        How far should the connector stick away from ports. The default is 5.

    Returns
    -------
    xpts : list
        X coordinates of the connector path.
    ypts : list
        Y coordinates of the connector path.

    """
    x0 = port1.x0;
    y0 = port1.y0;
    r0 = port1.angle();
    # Rotate all in the reference of port1
    p2dot = sm.make_dot(port2.x0, port2.y0)
    p2dot.rotate(x0, y0, -math.degrees(r0))
    x1 = p2dot.x-x0;
    y1 = p2dot.y-y0;
    if(abs(y1) < 0.005):
        xpts = [0,x1];
        ypts = [0,y1];
    else:
        aout = port2.angle()-r0%(2*math.pi);
        # offset
        xs = offset;
        xs1 = xs+3*offset;
        xe = x1+offset*math.cos(aout);
        ye = y1+offset*math.sin(aout);
        xe1 = xe+3*offset*math.cos(aout);
        ye1 = ye+3*offset*math.sin(aout);
    
        t = np.array([0,0.25,0.5,0.75,1]);
        xpts = np.power(1-t,3)*xs+3*np.power(1-t,2)*t*xs1+3*(1-t)*np.power(t,2)*xe1+np.power(t,3)*xe
        ypts = 3*(1-t)*np.power(t,2)*ye1+np.power(t,3)*ye;
        xpts = np.append([0],xpts);
        xpts = np.append(xpts,[x1])
        ypts = np.append([0],ypts);
        ypts = np.append(ypts,[y1])
        xpts = xpts.tolist()
        ypts = ypts.tolist()

    cost = math.cos(r0)
    sint = math.sin(r0)
    for i in range(len(xpts)):
        x=xpts[i]
        y=ypts[i]
        xpts[i]=cost*(x)-sint*(y)+x0
        ypts[i]=sint*(x)+cost*(y)+y0
    
    return xpts,ypts