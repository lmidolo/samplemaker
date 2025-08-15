/******************************************************************************
 * This file is part of sample_maker
 *
 *  
 ******************************************************************************/

#include "boopy_ffi.h"
#include <iostream>
#include <vector>
#include <boost/polygon/polygon.hpp>

#ifdef WIN32
#define STRDUP _strdup
#else
#define STRDUP strdup
#endif

#define MAX_ADDR 8

namespace gtl = boost::polygon;
using namespace boost::polygon::operators;

typedef gtl::polygon_data<int> Polygon;
typedef gtl::polygon_traits<Polygon>::point_type Point;
typedef std::vector<gtl::polygon_data<int> > PolygonSet;

namespace {
	unsigned int c_addr_ = 0;
	std::vector<PolygonSet> psets_(MAX_ADDR);
}

void bp_setGroupAddress(const unsigned int addr) {
	c_addr_ = (addr>=MAX_ADDR)?(MAX_ADDR-1):addr;
}

void bp_addPolyData(const int* data, unsigned int size) {
	size_t npts = size/2;
    Point *pts = new Point[npts];
    for(unsigned int i = 0; i< npts; i++) {
		pts[i]=gtl::construct<Point>(data[2*i],data[2*i+1]);
    }
    Polygon poly;
    gtl::set_points(poly,pts,pts+npts);

    psets_[c_addr_].push_back(poly);
    delete [] pts;
}

unsigned int bp_getPolyCount(void) {
	return static_cast<unsigned int>(psets_[c_addr_].size());
}

unsigned int bp_getPolySize(unsigned int n) {
	if(n<psets_[c_addr_].size()) {
		Polygon poly = psets_[c_addr_][n];
		return static_cast<unsigned int>(2*poly.size());
	} 
	return 0;
}

void bp_getPoly(int *data, unsigned int size, unsigned int n) {
	if(n<psets_[c_addr_].size()) {
        Polygon poly = psets_[c_addr_][n];
        int i = 0;
		for(auto v = poly.begin(); v!=poly.end(); v++) {
            data[i] = v->x();
			data[i+1] = v->y();
			i+=2;
        }
    }
}

double bp_area(void) {
	return gtl::area(psets_[c_addr_]);
}

void bp_clear(void) {
	gtl::clear(psets_[c_addr_]);
}

bool bp_empty(void) {
	return gtl::empty(psets_[c_addr_]);
}

void bp_difference(unsigned int addr) {
	if(addr<MAX_ADDR) {
		psets_[c_addr_]-=psets_[addr];
	}
}

void bp_intersection(unsigned int addr) {
	if(addr<MAX_ADDR) {
		psets_[c_addr_]&=psets_[addr];
	}
}

void bp_merge(unsigned int addr) {
	if(addr<MAX_ADDR) {
		psets_[c_addr_]+=psets_[addr];
	}
}

void bp_assign(void) {
	gtl::assign(psets_[c_addr_],psets_[c_addr_]);
}

void bp_exor(unsigned int addr) {
	if(addr<MAX_ADDR) {
		psets_[c_addr_]^=psets_[addr];
	}
}

void bp_trapezoids(void) {
	PolygonSet psin = psets_[c_addr_];
    bp_clear();
    gtl::get_trapezoids(psets_[c_addr_],psin);
}

void bp_resize(double value, bool corner_fill_arc, unsigned int num_circle_segments) {
	psets_[c_addr_]=gtl::resize(psets_[c_addr_],value,corner_fill_arc,num_circle_segments);
}