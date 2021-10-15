# -*- coding: utf-8 -*-
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
            
    
            