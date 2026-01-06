# Building SampleMaker

This document explains how to build SampleMaker with its C++ extension module (boopy) for different platforms.

## Overview

SampleMaker includes a C++ component called "boopy" that provides high-performance Boolean polygon operations using 
Boost.Polygon and is exposed to Python via pybind11. The project uses:

- **[scikit-build-core](https://scikit-build-core.readthedocs.io/en/latest/)**: 
  Modern build system that uses CMake and pure `pyproject.toml` configuration.
- **[CMake](https://cmake.org/)**: For configuring the C++ extension build.
- **[Astral uv](https://docs.astral.sh/uv/)**: For faster dependency installation during builds.
- **[cibuildwheel](https://cibuildwheel.pypa.io/en/stable/)**: 
  For cross-platform wheel building.


## Local Development Build

### Prerequisites
- Python 3.10 or later
- CMake 3.15 or later
- A C++14-compatible compiler
- pybind11 (installed automatically during build)
- Boost (header-only, for polygon operations)

### Linux

Install the required packages using your distribution's package manager:
```bash
# Ubuntu/Debian
sudo apt-get install build-essential cmake libboost-dev

# RHEL/CentOS/Fedora
sudo yum install gcc-c++ make cmake boost-devel
```

Navigate to the project directory and build:
```bash
# Using Astral uv (recommended)
uv sync

# Using pip
pip install -e .
```

### macOS

Install the required packages using Homebrew:
```bashbash
brew install cmake boost
```

Navigate to the project directory and build:
```bash
# Using Astral uv (recommended)
uv sync
# Using pip
pip install -e .
```

### Windows
To build on Windows, ensure you have Visual Studio with C++ build tools installed.

Boost can be installed via vcpkg:
```powershell
git clone https://github.com/Microsoft/vcpkg.git C:\vcpkg
C:\vcpkg\bootstrap-vcpkg.bat
C:\vcpkg\vcpkg.exe install boost-polygon
C:\vcpkg\vcpkg.exe integrate install
```

> [!NOTE]  
> `vcpkg` may come pre-installed with your Visual Studio installation. This version
> only works in manifest mode, meaning the above commands will not work. Ensure you
> are referencing the correct `vcpkg` installation.

Open "x64 Native Tools Command Prompt for VS" and navigate to the project directory:
```cmd
cd path\to\samplemaker
set CMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake

# Astral uv (recommended)
uv sync

# Using pip
pip install -e .
```

If boost is not found, try setting the CMAKE_TOOLCHAIN_FILE directly in the build command:
```cmd
cd path\to\samplemaker

# Astral uv (recommended)
uv sync -C cmake.args="-DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake"

# Using pip
pip install -e . -C cmake.args="-DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake"
```

## Building Wheels for Distribution

To build wheels for distribution, we use `cibuildwheel`. This tool automates 
the process of building wheels for multiple platforms and is intended to run
in CI environments.

This section outlines the steps to build wheels locally using `cibuildwheel`.

### Prerequisites
Ensure you are able to build the project locally as described in the previous section.

### Linux
Building Linux wheels locally requires [Docker](https://docs.docker.com/get-docker/).
If you are building using WSL2 on Windows, Docker Desktop should be installed on Windows.
For more information on working with Docker for WSL, see the official [Docker docs article](https://docs.docker.com/desktop/features/wsl/).

Once Docker is set up, you can build the wheels using the following command in the project directory:
```bash
# Using Astral uv (recommended)
uvx cibuildwheel .

# Using pip
pip install cibuildwheel
cibuildwheel .
```

### macOS
On macOS, you can build wheels directly without Docker. Run the following command in the project directory:
```bash
# Using Astral uv (recommended)
uvx cibuildwheel .

# Using pip
pip install cibuildwheel
cibuildwheel .
```

### Windows
To build Windows wheels locally, the correct version of `vcpkg` must be added to the PATH environment variable.
When using "x64 Native Tools Command Prompt for VS", the wrong version of `vcpkg` may be added to PATH.

To ensure the correct version is used, modify the PATH variable in the command prompt before building:
```cmd
set PATH=C:\vcpkg;%PATH%

# Using Astral uv (recommended)
uvx cibuildwheel .

# Using pip
pip install cibuildwheel
cibuildwheel .
```