#include <iostream>
#include <vector>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <pybind11/stl_bind.h>
#include <boost/polygon/polygon.hpp>

namespace py = pybind11;
namespace gtl = boost::polygon;
using namespace boost::polygon::operators;

typedef gtl::polygon_data<int> Polygon;
typedef gtl::polygon_traits<Polygon>::point_type Point;
typedef std::vector<gtl::polygon_data<int> > PolygonSet;

struct PolyGroup {
    void addPolyData(const std::vector<int> &data) {
        size_t npts = (data.size())/2;
        Point *pts = new Point[npts];
        for(unsigned int i = 0; i< npts; i++) {
            pts[i]=gtl::construct<Point>(data.at(2*i),data.at(2*i+1));
        }
        Polygon poly;
        gtl::set_points(poly,pts,pts+npts);

        ps_.push_back(poly);
        delete [] pts;
    }
    unsigned int getPolyCount(void) {return static_cast<unsigned int>(ps_.size());}
    const std::vector<int> getPoly(unsigned int n) const {
        std::vector<int> pseq;
        if(n<ps_.size()) {
            Polygon poly = ps_[n];
            for(auto v = poly.begin(); v!=poly.end(); v++) {
                pseq.push_back(v->x());
                pseq.push_back(v->y());
            }
        }
        return pseq;
    }
    double area() {
        return gtl::area(ps_);
    }
    void clear() {
        gtl::clear(ps_);
    }
    bool empty() {
        return gtl::empty(ps_);
    }
    void difference(PolyGroup &pg2) {
        ps_-=pg2.ps_;
    }
    void intersection(PolyGroup &pg2) {
        ps_&=pg2.ps_;
    }
    void merge(PolyGroup &pg2) {
        ps_+=pg2.ps_;
    }
    void assign() {
        gtl::assign(ps_,ps_);
    }
    void exor(PolyGroup &pg2) {
        ps_^=pg2.ps_;
    }
    void trapezoids() {
        PolygonSet psin = ps_;
        clear();
        gtl::get_trapezoids(ps_,psin);
    }
    void resize(double value, bool corner_fill_arc, unsigned int num_circle_segments) {
        ps_=gtl::resize(ps_,value,corner_fill_arc,num_circle_segments);
    }

    PolygonSet ps_;
};

PYBIND11_MODULE(boopy, m) {
    py::class_<PolyGroup>(m, "PolyGroup")
        .def(py::init<>())
        .def("addPolyData",&PolyGroup::addPolyData)
        .def("getPolyCount", &PolyGroup::getPolyCount)
        .def("getPoly", &PolyGroup::getPoly)
        .def("area", &PolyGroup::area)
        .def("clear", &PolyGroup::clear)
        .def("empty", &PolyGroup::empty)
        .def("assign", &PolyGroup::assign)
        .def("difference", &PolyGroup::difference)
        .def("intersection", &PolyGroup::intersection)
        .def("merge", &PolyGroup::merge)
        .def("exor", &PolyGroup::exor)
        .def("trapezoids", &PolyGroup::trapezoids)
        .def("resize", &PolyGroup::resize);
}
