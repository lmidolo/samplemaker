"""
Binary export to GDS files.

The `GDSWriter` class should not be used directly but via the `samplemaker.layout.Mask` object
in the `samplemaker.layout` submodule.

"""

import math
import numpy as np
import struct
import time
import samplemaker.shapes as smsh
from samplemaker.shapes import GeomGroup


class GDSWriter:
    """
    GDS output class
    """
    
    def __init__(self, circleres: int = 12, arcres: int = 32):
        """
        Initialize the GDSWriter class

        Parameters
        ----------
        circleres : int, optional
            Number of points to use for circles. The default is 12.
        arcres : int, optional
            Number of points to use for round elements (ellipses, rings, arcs). The default is 32.

        Returns
        -------
        None.

        """
        self.circleres=circleres
        self.arcres=arcres
        self.xc = np.array([0.]*circleres)
        self.yc = np.array([0.]*circleres)
        for i in range(circleres):
            self.xc[i]=math.cos(i*2*math.pi/circleres)
            self.yc[i]=math.sin(i*2*math.pi/circleres)
        #Init stuff goes here
        
        
    def __write_string(self,text,tag):
        L=len(text)
        self.fid.write(struct.pack(">2H",L+L%2+4,tag));
        self.fid.write(text.encode());
        if(L%2==1):
            self.fid.write(struct.pack('b',0))
            
    def __write_real8(self,value):
        num = value if value>=0 else -value
        exponent = math.floor(-math.log2(num)/4)
        mantissa = num*math.pow(2,4*exponent)*math.pow(2,56)
        real = [0]*8
        real[0]=(64-exponent) | (128 if value<0 else 0)
        for i in range(6,-1,-1):
            real[6-i+1]=math.floor(mantissa/math.pow(2,8*i))
            mantissa-=real[6-i+1]*math.pow(2,8*i)        
        self.fid.write(struct.pack('8B',*real))
                   
    def __write_data(self, data):
        self.fid.write(data)
        
    def __write_polygon(self,poly):
        if(poly.layer<0): return
        pdata = poly.int_data()
        buf = np.array([4,0x0800,6,0x0D02,poly.layer,6,0x0E02,0,4*len(pdata)+4,0x1003]);
        self.fid.write(struct.pack(f">{buf.size}H",*buf))
        self.fid.write(struct.pack(f">{pdata.size}i",*pdata))
        self.fid.write(struct.pack(">2H",4,0x1100))
    
    def __write_circle(self,circ):
        self.__write_polygon(smsh.Poly(circ.r*self.xc+circ.x0,circ.r*self.yc+circ.y0,circ.layer))
                
    def __write_path(self,path):
        buf = np.array([4,0x0900,6,0x0D02,path.layer,6,0x0E02,0,6,0x2102,1,8,0x0F03]);
        self.fid.write(struct.pack(f">{buf.size}H",*buf))
        self.fid.write(struct.pack(">i",math.floor(path.width*1000)))
        self.fid.write(struct.pack(">2H",8*len(path.xpts)+4,0x1003))
        data = np.transpose(np.round(np.array([path.xpts,path.ypts])*1000).astype(int)).reshape(-1)
        self.fid.write(struct.pack(f">{data.size}i",*data))
        self.fid.write(struct.pack(">2H",4,0x1100))
        
    def __write_text(self,text):
        if(text.text.replace(" ","")==""):
            return
        buf = np.array([4,0x0C00,  6,0x0D02,text.layer,
                        6,0x1602,0,6,0x1701,text.posu+text.posv*4+16,
                        8,0x0F03]);
        self.fid.write(struct.pack(f">{buf.size}H",*buf))
        self.fid.write(struct.pack(">i",math.floor(text.width*1000)))
        self.fid.write(struct.pack(">2H",12,0x1003))
        self.fid.write(struct.pack(">2i",
                                   math.floor(text.x0*1000),
                                   math.floor(text.y0*1000)))
        L=len(text.text)
        self.fid.write(struct.pack(">2H",L+4,0x1906))
        self.fid.write(text.text.encode())
        self.fid.write(struct.pack(">2H",4,0x1100))
        
    def __write_strans(self,mag,angle,mirror):
        if(mag==1 and angle==0 and mirror==0):
            return
        strans = 0
        if(mirror):
            strans=1<<15
        #if(mag!=1):
        #    strans+=4
        #if(angle!=0):
        #    strans+=2
        buf = np.array([6,0x1A01,strans])
        self.fid.write(struct.pack(f">{buf.size}H",*buf))
        if(mag!=1):
             self.fid.write(struct.pack(">2H",12,0x1B05))
             self.__write_real8(mag)
        if(angle!=0):
             self.fid.write(struct.pack(">2H",12,0x1C05))
             self.__write_real8(angle)      
    
    def __write_sref(self,sref):
        self.fid.write(struct.pack(">2H",4,0x0A00))
        self.__write_string(sref.cellname, 0x1206)
        self.__write_strans(sref.mag,sref.angle,sref.mirror)
        self.fid.write(struct.pack(">2H",12,0x1003))
        self.fid.write(struct.pack(">2i",
                                   int(round(sref.x0*1000)),
                                   int(round(sref.y0*1000))))
        self.fid.write(struct.pack(">2H",4,0x1100))
        
    def __write_aref(self,aref):
        self.fid.write(struct.pack(">2H",4,0x0B00))
        self.__write_string(aref.cellname, 0x1206)
        self.__write_strans(aref.mag,aref.angle,aref.mirror)
        self.fid.write(struct.pack(">4H",8,0x1302,
                                   math.floor(aref.ncols),
                                   math.floor(aref.nrows)))
        self.fid.write(struct.pack(">2H",28,0x1003))
        self.fid.write(struct.pack(">2i",
                                   int(round(aref.x0*1000)),
                                   int(round(aref.y0*1000))))
        self.fid.write(struct.pack(">2i",
                                   math.floor((aref.x0+aref.ax*aref.ncols)*1000),
                                   math.floor((aref.y0+aref.ay*aref.ncols)*1000)))
        self.fid.write(struct.pack(">2i",
                                   math.floor((aref.x0+aref.bx*aref.nrows)*1000),
                                   math.floor((aref.y0+aref.by*aref.nrows)*1000)))
        self.fid.write(struct.pack(">2H",4,0x1100))
                       
    def __large_polygons(self,gg: "GeomGroup"):
        group = [];
        for geom in gg.group:
            geomtype = type(geom);
            if(geomtype==smsh.Poly):
                if(geom.Npts>8000):
                    newgrp = GeomGroup()
                    newgrp.add(geom)
                    newgrp.trapezoids(geom.layer)
                    group+=newgrp.group;
                    continue
            group+=[geom]
        gg.group=group
        return gg
        
    def open_library(self,filename: str):
        """
        Opens a new GDS file for writing. To close, call close_library()

        Parameters
        ----------
        filename : str
            The name of the file to write into.

        Returns
        -------
        None.

        """
        self.fid = open(filename,"wb")
        #Write header
        lt=time.localtime(time.time())
        buf = np.array([6,2,3,28,258,lt.tm_year,lt.tm_mon,lt.tm_mday,lt.tm_hour,lt.tm_min,lt.tm_sec,lt.tm_year,lt.tm_mon,lt.tm_mday,lt.tm_hour,lt.tm_min,lt.tm_sec]);
        self.fid.write(struct.pack(f">{buf.size}H",*buf));
        # Library name
        self.__write_string(filename,518)
        # Units
        self.fid.write(struct.pack(">2H",20,0x0305));
        self.__write_real8(1e-3); 
        self.__write_real8(1e-9);
        
        print("Opened " + filename)
        
        
    def open_structure(self,structure_name: str):
        """
        Opens a new structure (or cell) in the existing GDS stream.
        The file should be already open using open_library()
        This function can be used to write multiple objects in a single cell.
        It should be closed with close_structure()

        Parameters
        ----------
        structure_name : str
            A string with a valid GDS cell/structure name.

        Returns
        -------
        None.

        """
        print("Writing structure: " + structure_name)
        lt=time.localtime(time.time())
        buf = np.array([28,1282,lt.tm_year,lt.tm_mon,lt.tm_mday,lt.tm_hour,lt.tm_min,lt.tm_sec,lt.tm_year,lt.tm_mon,lt.tm_mday,lt.tm_hour,lt.tm_min,lt.tm_sec]);
        self.fid.write(struct.pack(f">{buf.size}H",*buf));
        self.__write_string(structure_name,1542)
        
    def write_geomgroup(self,geom_group: GeomGroup):
        """
        Writes a GeomGroup to GDS stream. The file should be first opened with
        open_library() followed by open_structure().
        To be used for interactive writing only. See write_structure() for 
        direct writing (recommended)

        Parameters
        ----------
        geom_group : samplemaker.shapes.GeomGroup
            The geometry to be written into GDS format.

        Returns
        -------
        None.

        """
        geom_group = self.__large_polygons(geom_group)
        for geom in geom_group.group:
            geomtype = type(geom);
            if(geomtype==smsh.Poly):
                self.__write_polygon(geom)
                continue
            if(geomtype==smsh.Circle):
                self.__write_circle(geom)
                continue
            if(geomtype==smsh.Path):
                self.__write_path(geom)
                continue
            if(geomtype==smsh.Text):
                self.__write_text(geom)
                continue
            if(geomtype==smsh.SRef):
                self.__write_sref(geom)
                continue
            if(geomtype==smsh.ARef):
                self.__write_aref(geom)
                continue
            if(geomtype==smsh.Ellipse):
                g = geom.to_polygon(self.arcres)
                self.__write_polygon(g.group[0]) # produces one geometry only
                continue
            if(geomtype==smsh.Ring):
                g = geom.to_polygon(self.arcres)
                self.__write_polygon(g.group[0]) # produces one geometry only
                continue
            if(geomtype==smsh.Arc):
                g = geom.to_polygon(self.arcres)
                self.__write_polygon(g.group[0]) # produces one geometry only
                continue
        
    def close_structure(self):
        """
        Closes the structure, should be called after open_structure()

        Returns
        -------
        None.

        """
        self.fid.write(struct.pack(">2H",4,1792));
        
    def write_structure(self,structure_name: str,geom_group: 'GeomGroup'):
        """
        Write a GeomGroup into a named structure/cell. The GeomGroup is written
        into the cell once and then the GDS cell is closed.
        This is equivalent to 
            open_structure(structure_name)
            write_geomgroup(geom_group)
            close_structure()

        Parameters
        ----------
        structure_name : str
            A string with a valid GDS structure/cell name.
        geom_group : 'GeomGroup'
            The GeomGroup to be written into GDS format.

        Returns
        -------
        None.

        """
        self.open_structure(structure_name)
        self.write_geomgroup(geom_group)
        self.close_structure()
        
    def write_pool(self,pool: dict):
        """
        Writes all the structures in the dictionary using key name as structure
        reference name and value as the group to be written.

        Parameters
        ----------
        pool : dict
            A dictionary containing structure names as keys and GeomGroup as values.

        Returns
        -------
        None.

        """
        for sname,group in pool.items():
            self.write_structure(sname, group)
            
    def write_pool_use_cache(self,pool: dict, cache: dict):
        """
        Writes all the structures in the dictionary using key name as structure
        reference name and value as the group to be written.
        Uses GDS cache when available

        Parameters
        ----------
        pool : dict
            A dictionary containing structure names as keys and GeomGroup as values.
        cache: dict
            A dictionary containing structure names as keys and binary GDS data as values.

        Returns
        -------
        None.

        """
        for sname,group in pool.items():
            if sname in cache.keys():
                print("Writing cached",sname)
                self.__write_data(cache[sname])
            else:
                self.write_structure(sname, group)
        
    def close_library(self):
        """
        Closes the GDS library and the file stream

        Returns
        -------
        None.

        """
        self.fid.write(struct.pack('>2H',4,1024));
        pos = self.fid.tell()
        buf = np.zeros(2048-pos%2048,dtype=int);
        self.fid.write(struct.pack(f"{buf.size}b",*buf))
        print('Writing to GDS complete.')
        self.fid.close()
        
    
