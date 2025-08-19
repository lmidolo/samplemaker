# -*- coding: utf-8 -*-
"""
Boolean operations from Boost-Polygon library and FFI 

This code replaces the old pybind library and should work directly on 
any Python version
    
"""

from ctypes import *
import os
import numpy as np
import itertools

# class libhandle():
#     def __init__(self):
        
#         dll_lib_path = os.path.join(os.path.dirname(__file__),"boopy_ffi.dll")
#         self.__bpdll__ = cdll.LoadLibrary(dll_lib_path)
#         self.__bpdll__.bp_addPolyData.argtypes = [np.ctypeslib.ndpointer(dtype=np.int32, ndim=1,flags="C"), c_size_t]

#     def __del__(obj):
#         print("Called")

# test = libhandle()
dll_lib_path = os.path.join(os.path.dirname(__file__),"boopy_ffi.dll")
__bpdll__ = cdll.LoadLibrary(dll_lib_path)
__bpdll__.bp_addPolyData.argtypes = [np.ctypeslib.ndpointer(dtype=np.int32, ndim=1,flags="C"), c_size_t]
class PolyGroup():
    def __init__(self, addr: int):
        self.addr = addr   
        self.clear();
        
    def addPolyData(self, pdata):
        __bpdll__.bp_setGroupAddress(c_uint(self.addr))
        __bpdll__.bp_addPolyData(pdata.astype(np.int32),pdata.size)
        
    def getPolyCount(self):
        __bpdll__.bp_setGroupAddress(c_uint(self.addr))
        return __bpdll__.bp_getPolyCount()
    
    def getPoly(self, index: int):
        __bpdll__.bp_setGroupAddress(c_uint(self.addr))
        dsize = __bpdll__.bp_getPolySize(c_uint(index))
        p = (c_int*dsize)()
        __bpdll__.bp_getPoly(p,c_uint(dsize),c_uint(index))
        return p

    def area(self):
        __bpdll__.bp_setGroupAddress(c_uint(self.addr))
        return __bpdll__.bp_area()
    
    def clear(self):
        __bpdll__.bp_setGroupAddress(c_uint(self.addr))
        __bpdll__.bp_clear()
    
    def empty(self):
        __bpdll__.bp_setGroupAddress(c_uint(self.addr))
        return __bpdll__.bp_empty()
    
    def difference(self, pg2: 'PolyGroup'):
        __bpdll__.bp_setGroupAddress(c_uint(self.addr))
        __bpdll__.bp_difference(c_uint(pg2.addr))
    
    def merge(self, pg2: 'PolyGroup'):
        __bpdll__.bp_setGroupAddress(c_uint(self.addr))
        __bpdll__.bp_merge(c_uint(pg2.addr))
        
    def intersection(self, pg2: 'PolyGroup'):
        __bpdll__.bp_setGroupAddress(c_uint(self.addr))
        __bpdll__.bp_intersection(c_uint(pg2.addr))
        
    def exor(self, pg2: 'PolyGroup'):
        __bpdll__.bp_setGroupAddress(c_uint(self.addr))
        __bpdll__.bp_exor(c_uint(pg2.addr))
        
    def assign(self):
        __bpdll__.bp_setGroupAddress(c_uint(self.addr))
        __bpdll__.bp_assign()
    
    def trapezoids(self):
        __bpdll__.bp_setGroupAddress(c_uint(self.addr))
        __bpdll__.bp_trapezoids()
    
    def resize(self, value: float,  corner_fill_arc: bool, num_circle_segments: int):
        __bpdll__.bp_setGroupAddress(c_uint(self.addr))
        __bpdll__.bp_resize(c_double(value),c_bool(corner_fill_arc), c_uint(num_circle_segments))
        

    