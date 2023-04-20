Instructions on how to compile on MAC:

1.	Install Spyder with Conda (or similar): https://docs.spyder-ide.org/current/installation.html
2.	Verify/set python to correct version (3.8): 
	a.	To check the current version, type in terminal: “python --version”.
	b.	To install Python 3.8, type in terminal: “conda create -n py38 python=3.8 anaconda”.
	c.	To activate this version, type in terminal: “conda activate py38”.
	d.	Set this as default in Spyder: Go to preferences (“CMD" + ",”) -> "Python interpreter” -> “Use the following python interpreter”, type path to python. 
		To get path, type in terminal “which python” (in a session where the version is already activated to 3.8).
3.	Using macports (download and install with package for your OS version, see https://www.macports.org/install.php). Alternatively, use homebrew (https://brew.sh/) – the instructions below are for macports. 
	a.	Install cmake, type in terminal “sudo port install cmake” (authorize with normal password).
	b.	Install boost, type in terminal “sudo port install boost” (authorize with normal password).
	c.	Install pybind11, type in terminal “sudo port install pybind11” (authorize with normal password).
4.	Clone the git repo to appropriate folder, e.g., “~/Documents/software/samplemaker”. 
5.	Compile boopy.so binary library: 
	a.	Navigate to the src-folder, type in terminal: “cd samplemaker/src/boopy”.
	b.	Verify python version 3.8 is used, type in terminal: “python --version”. If not, set using “conda activate py38”.
	c.	Run cmake, type in terminal: “cmake . -DPYTHON_EXECUTABLE=$(which python3)”.
	d.	Run make, type in terminal: “make”. This produces a binary “.so” file, e.g., "boopy.cpython-38-darwin.so”. 
	e.  	Rename this to “boopy.so” and place it in “samplemaker/src/samplemaker/resources/“.
6.	Verify the tutorials work by running them from Spyder (set working directory to “samplemaker/src”).

Thanks to Marcus Albrechtsen (Niels Bohr Institute) for the instructions.