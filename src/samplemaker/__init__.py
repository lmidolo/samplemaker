"""
.. figure:: gfx/SampleMaker_logo_rainbow.png
This is the Python version of Sample Maker, a scripting tool for designing 
lithographic masks in the GDSII format. Package `samplemaker` comes 
with different tools and submodules for the creation and manipulation of basic
shapes, periodic shapes, sequences (e.g. waveguides), circuits, and complex 
devices. 

The code has been developed primarily for nanophotonics, but it can be easily
extended to different applications in micro and nano device fabrication.

Sample Maker is developed and maintained by Leonardo Midolo (Niels Bohr Institute,
University of Copenhagen). It is based on the MATLAB(R) code developed by Leonardo Midolo 
between 2013 and 2019. The first version of the rewritten Python code has been released in September 2021.

.. include:: ./documentation.md
"""

from typing import (  # noqa: F401
    cast, Any, Callable, Dict, Generator, Iterable, List, Mapping, NewType,
    Optional, Set, Tuple, Type, TypeVar, Union,
)

try:
    from samplemaker._version import version as __version__  # noqa: F401
except ImportError:
    __version__ = '???'  # Package not installed
    
__pdoc__: Dict[str, Union[bool, str]] = {}
__pdoc__["samplemaker.Tutorials"]=False
__pdoc__["samplemaker.tests"]=False
__pdoc__["samplemaker.resources"]=False
__pdoc__["samplemaker.gdsreader"]=False
__pdoc__["samplemaker.devices.DevicePort"]=False

# The LayoutPool contains all the current layout, this class should generally not
# be used directly, but only through the Mask class.
LayoutPool = dict() # connects a SREF name to a particular geomgroup in the current memory
# Additional cache pool
_DevicePool = dict() # connects a device hash to a SREF to be instantiated
_DeviceLocalParamPool = dict() # connects a device hash to local parameters created by the call to geom()
_DeviceCountPool = dict() # connects a device name to a device count 