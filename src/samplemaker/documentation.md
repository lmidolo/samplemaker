Code structure
--------------

### Learning `samplemaker`
The best way to learn `samplemaker` is to use the tutorials provided in the package distribution folder. 
The library use mostly object-oriented programming and it is subdivided in several submodules.

Base modules include: 

* `samplemaker.layout`
        Classes for defining the layout of the mask file.
        
* `samplemaker.shapes`
        Classes that define all the basic shape object (e.g. polygons, circles,...).
        
* `samplemaker.makers`
        Helper functions to generate basic shapes into `GeomGroup` objects. 

* `samplemaker.gdswriter` 
        Classes for handling the output to the GDSII file format.
           
* `samplemaker.viewers` 
        Functions (based on [`matplotlib`][matplotlib]) for the graphical inspection the layout. 
[matplotlib]: https://matplotlib.org/

Advanced modules for nanophotonics include:
        
* `samplemaker.phc`
        Classes and functions to generate periodic structures (e.g. photonic crystals).
        
* `samplemaker.sequencer`
        Classes to handle custom sequences of shapes (e.g. waveguides).
        
* `samplemaker.devices`
        Base classes for handling device objects which can be arranged into circuits.
        
### Binary files

`samplemaker` uses a pre-compiled binary module called `boopy` built with [`pybind11`][pybind11] to perform boolean
operations between polygons. These functions are derived from the [Boost Polygon] libraries
developed by Lucanus Simonson and Andrii Sydorchuk.
A pre-compiled version of `boopy` for Windows 64 bit and Python 3.8 is distributed with the module.
The C++ source code is also distributed and can be modified/re-compiled, if necessary.
[pybind11]: https://pybind11.readthedocs.io/en/stable/
[Boost Polygon]: https://www.boost.org/doc/libs/1_77_0/libs/polygon/doc/index.htm


Compatibility
------------
`samplemaker` requires Python 3.8.

       
Contributing
------------
`samplemaker` is [on GitHub]. Bug reports are welcome.

[on GitHub]: https://github.com/lmidolo/samplemaker

License
-------
`samplemaker` is licensed under the terms of the 3-clause BSD License [BSD-3-clause]{: rel=license},
meaning you can use it for any purpose (including commercial) and remain in
complete ownership of all the files you produce.

[BSD-3-clause]: https://opensource.org/licenses/BSD-3-Clause
