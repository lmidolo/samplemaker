# -*- coding: utf-8 -*-
"""
Base device library.

This is a collection of some simple demo devices distributed with the base
version of `samplemaker`. It can be used as template for creating new libraries
or to learn how to design them.

Note that individual device methods are not documented but should be readable 
and self-explanatory.

The library provides the following devices:
    
"""

import numpy as np
from samplemaker.devices import Device, registerDevicesInModule
import samplemaker.makers as sm
from samplemaker.baselib.waveguides import BaseWaveguideSequencer, BaseWaveguidePort

class CrossMark(Device):
    def initialize(self):
        self.set_name("BASELIB_CMARK")
        self.set_description("Generic cross marker for mask alignment.")
    
    def parameters(self):
        self.addparameter("length1", 20, "Length of inner cross",float)
        self.addparameter("length2", 10, "Length of outer cross",float)
        self.addparameter("width1", 0.5, "Width of inner cross", float)
        self.addparameter("width2", 2, "width of outer cross", float)
        self.addparameter("layer", 4, "Layer to use for cross", int,(0,255))
        self.addparameter("mark_number",0,"Places a square in the corner, use 0 to remove", float, (0,4))
        self.addparameter("square_size",10,"Size of the square in the corner", float)
        
    def geom(self):
        p = self.get_params();
        cross = sm.make_rect(0, 0, p["length1"], p["width1"],layer=1)
        cross += sm.make_rect(0, 0, p["width1"], p["length1"],layer=1)
        cross.boolean_union(1)
        ocross = sm.make_rect(p["length1"]/2,0,p["length2"],p["width2"],numkey=4)
        for i in range(4):
            c = ocross.copy()
            c.rotate(0, 0, 90*i)
            cross+=c
        if(p["mark_number"]>0):
            rot = 90*(p["mark_number"]-1)
            square = sm.make_rect(p["length1"]/2+p["length2"],
                                  p["length1"]/2+p["length2"],
                                  p["square_size"],p["square_size"],numkey=1)
            square.rotate(0,0,rot)
            cross+=square
            
        cross.set_layer(p["layer"])
        return cross

class DirectionalCoupler(Device):
    def initialize(self):
        self.set_name("BASELIB_DCPL")
        self.set_description("Simple symmetric directional coupler")
    
    def parameters(self):
        self.addparameter("length", 20, "Coupling length",float)
        self.addparameter("width", 0.3, "Width of the waveguides in the coupling section",float,(0.01,1))
        self.addparameter("gap", 0.5, "Distance between waveguides in the coupling section", float)
        self.addparameter("input_dist", 5, "Distance between waveguides at input", float,(0.01,np.infty))
        self.addparameter("input_len", 7, "Length of the input section from input to coupling", float, (3,np.infty))        
        
    def geom(self):
        p = self.get_params();
        # Draw the upper arm, then mirror
        off = p["input_dist"]/2
        clen = (p["input_len"]-1)/2
        Ltot = p["length"]+p["input_len"]*2
        seq = [['T',1,p["width"]],["C",-off,clen],
                ['S',p["length"]/2]]
        ss =  BaseWaveguideSequencer(seq)
        dc = ss.run()
        dc2 = dc.copy()
        dc2.mirrorX(Ltot/2)
        dc+=dc2
        dc.translate(-Ltot/2, off+p["gap"]/2+p["width"]/2)
        dc3 = dc.copy()
        dc3.mirrorY(0)
        dc+=dc3        
        # Add ports
        XP = Ltot/2
        YP = off+p["gap"]/2+p["width"]/2
        self.addlocalport(BaseWaveguidePort(-XP, YP, "west", ss.options["defaultWidth"], "p1"))
        self.addlocalport(BaseWaveguidePort( XP, YP, "east", ss.options["defaultWidth"], "p2"))
        self.addlocalport(BaseWaveguidePort(-XP,-YP, "west", ss.options["defaultWidth"], "p3"))
        self.addlocalport(BaseWaveguidePort( XP,-YP, "east", ss.options["defaultWidth"], "p4"))
        
        return dc
        
# Register all devices here in this module
registerDevicesInModule(__name__)
