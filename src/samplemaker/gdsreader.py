"""
Binary import of GDS files. 

This class does not import GDS files directly into geometries. 
It only imports the binary streams for reuse.
Not to be used in actual scripts, unless it is for very special purposes.
"""

import math
import numpy as np
import struct
import time
import array
import os
from copy import deepcopy
import samplemaker.shapes as smsh
from samplemaker.shapes import GeomGroup
import samplemaker.makers as sm

class GDSRecord:
    def __init__(self,size: int, rectype: int, datatype: int, bheader, data=""):
        self.size = size
        self.rectype = rectype
        self.datatype = datatype
        self.bheader = bheader
        self.data = data
    
    def to_binary(self):
        if(self.size==4):
            return self.bheader
        else:
            return self.bheader+self.data
        

class GDSReader:
    """
    GDS input class
    """
    
    def __init__(self):
        self.buf = ''
        self.ptr = 0
        self.celldata=dict() # store binary GDS celldata
        
    def __read_rec(self,f):
        # Reads next record in file
        header = f.read(4)
        if not header or len(header)<4:
            return False
        htpl = struct.unpack(">Hbb",header)
        hlen = htpl[0];
        recdata = ""
        if hlen>4:
            recdata = f.read(hlen-4)
        return GDSRecord(hlen, htpl[1],htpl[2],header,recdata)
    
    def __read_rec_buf(self):
        htpl = struct.unpack(">Hbb",self.buf[self.ptr:(self.ptr+4)])
        hlen = htpl[0]
        self.ptr+=hlen
        return (htpl[1],self.ptr-hlen,hlen)
    
    def __read_real8(self, data):
        sign = 1
        if(data[0]>>7): 
            sign = -1
        ex = 64-data[0]%128
        mantissa = 0
        for i in range(6,-1,-1):
            mantissa+=data[6-i+1]*math.pow(2,8*i)
            
        
        return mantissa/math.pow(2,4*ex)/math.pow(2,56)
    
    def get_cell(self, cellname: str):
        if cellname not in self.celldata:
            print("Cellname",cellname,"does not exist in GDS record")
        
        gg = GeomGroup()
        
        self.buf = self.celldata[cellname]
        self.ptr=0
        cur_layer=0
        cur_width=0
        cur_el = 8; # BND
        cur_xy=[];
        cur_txt_posu = 0
        cur_txt_posv = 0
        cur_strans_mir = 0
        cur_strans_mag = 1
        cur_strans_angle = 0
        cur_string = ""
        cur_sname = ""
        cur_col = 1
        cur_row = 1
        
        while self.ptr<len(self.buf):
            (rtype,pos,hlen) = self.__read_rec_buf()
            if(hlen == 0): 
                break
            if(rtype==8): # BOUNDARY
                cur_el = 8
            if(rtype==9): # PATH
                cur_el = 9
                cur_width=0
            if(rtype==10): # SREF            
                cur_el = 10
                cur_sname = ""
                cur_strans_mir = 0
                cur_strans_mag = 1
                cur_strans_angle = 0
            if(rtype==11): # AREF            
                cur_el = 11
                cur_sname = ""
                cur_col = 1
                cur_row = 1
                cur_strans_mir = 0
                cur_strans_mag = 1
                cur_strans_angle = 0                

            if(rtype==12): # TEXT            
                cur_el = 12    
                cur_txt_posu = 0
                cur_txt_posv = 0
                cur_strans_mir = 0
                cur_strans_mag = 1
                cur_strans_angle = 0


            if(rtype==13): # LAYER
                data = self.buf[(pos+4):(pos+hlen)]
                cur_layer = struct.unpack(">H",data)[0];
            if(rtype==15): #WIDTH
                data = self.buf[(pos+4):(pos+hlen)]
                cur_width = float(struct.unpack(">i",data)[0])/1000;
            if(rtype==16): # XY
                data = self.buf[(pos+4):(pos+hlen)]
                npts = int(len(data)/4)
                cur_xy = np.array(struct.unpack(f">{npts}i",data))
            if(rtype==17): # ENDEL
                if(cur_el == 8): # Make a poly
                    p1 = smsh.Poly([0], [0], cur_layer)
                    p1.set_int_data(cur_xy);
                    gg.add(p1)
                if(cur_el == 9): # Make a path
                    xpts = np.copy(cur_xy[0::2]).astype(float)/1000
                    ypts = np.copy(cur_xy[1::2]).astype(float)/1000
                    gg+=sm.make_path(xpts, ypts, cur_width,layer=cur_layer)  
                if(cur_el == 10): # Make a SREF
                    r1 = smsh.SRef(cur_xy[0].astype(float)/1000,
                                   cur_xy[1].astype(float)/1000, cur_sname, smsh.GeomGroup(), 
                                   cur_strans_mag, cur_strans_angle, cur_strans_mir)
                    gg.add(r1)
                if(cur_el == 11): # Make a AREF
                    pts =  np.copy(cur_xy).astype(float)/1000
                    x0 = pts[0]
                    y0 = pts[1]
                    ax = (pts[2]-x0)/cur_col
                    ay = (pts[3]-y0)/cur_col
                    bx = (pts[4]-x0)/cur_row
                    by = (pts[5]-y0)/cur_row
                    
                    a1 = smsh.ARef(x0,y0, cur_sname, smsh.GeomGroup(),cur_col,cur_row,ax,ay,bx,by,
                                   cur_strans_mag, cur_strans_angle, cur_strans_mir)
                    gg.add(a1)
                if(cur_el == 12): # Make text
                    t1 = smsh.Text(cur_xy[0].astype(float)/1000,
                                   cur_xy[1].astype(float)/1000,cur_string,cur_txt_posu,cur_txt_posv,
                                   cur_width*10,cur_width,cur_strans_angle,cur_layer)
                    gg.add(t1)    
            
            if(rtype == 18): #SNAME
                data = self.buf[(pos+4):(pos+hlen)]
                cur_sname = data.decode('ascii')
                if(cur_sname[-1]=='\x00'):
                    cur_sname=cur_sname[0:-1]
            if(rtype == 19): # COLROW
                data = self.buf[(pos+4):(pos+hlen)]
                colrw = struct.unpack(">2H",data);
                cur_col = colrw[0]
                cur_row = colrw[1]
            if(rtype==23): # TEXT PRESENTATION
                data = self.buf[(pos+4):(pos+hlen)]
                pres = struct.unpack(">H",data)[0];
                cur_txt_posu = (pres-16)%4
                cur_txt_posv = (pres-16)>>2
            if(rtype == 25): #STRING
                data = self.buf[(pos+4):(pos+hlen)]
                cur_string = data.decode('ascii')
                if(cur_string[-1]=='\x00'):
                    cur_string=cur_string[0:-1]

            if(rtype==26): # STRANS
                data = self.buf[(pos+4):(pos+hlen)]
                strans = struct.unpack(">H",data)[0];
                cur_strans_mir=strans>>15
                cur_strans_mag = 1
                cur_strans_angle = 0
            
            if(rtype==27): # MAG
                data = self.buf[(pos+4):(pos+hlen)]
                real = struct.unpack("8B",data);
                cur_strans_mag = self.__read_real8(real)
            
            if(rtype==28): # ANGLE
                data = self.buf[(pos+4):(pos+hlen)]
                real = struct.unpack("8B",data);
                cur_strans_angle = self.__read_real8(real)
                
        return gg
        
    def quick_read(self, filename: str):
        """
        Performs a quick scan of the GDS file and stores
        structures (between BGNSTR and ENDSTR) in memory

        Parameters
        ----------
        filename : str
            The gds file name.

        Returns
        -------
        None.

        """

        with open(filename,'rb') as f:
            self.buf=f.read()
        
        bgnstr = -1
        cellname = ''
        while self.ptr<len(self.buf):
            (rtype,pos,hlen) = self.__read_rec_buf()
            if(hlen == 0): 
                break
            if(rtype == 5): #BGNSTR
                bgnstr=pos
            if(rtype == 6): #STRNAME
                data = self.buf[(pos+4):(pos+hlen)]
                cellname = data.decode('ascii')
                if(cellname[-1]=='\x00'):
                    cellname=cellname[0:-1]
                
            if(rtype == 7): #ENDSTR
                self.celldata[cellname]=deepcopy(self.buf[bgnstr:self.ptr])
            
        del self.buf
            
    
            