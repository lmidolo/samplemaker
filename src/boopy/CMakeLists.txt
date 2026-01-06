cmake_minimum_required(VERSION 3.15...3.29)
project(${SKBUILD_PROJECT_NAME} LANGUAGES CXX)

# Find Python
find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)

# Find pybind11
find_package(pybind11 CONFIG REQUIRED)

# Find Boost
if(WIN32)
    # On Windows with vcpkg, use CONFIG mode only
    find_package(Boost REQUIRED CONFIG)
else()
    # On Linux/macOS, try CONFIG first, fall back to MODULE mode
    find_package(Boost QUIET CONFIG)
    if(NOT Boost_FOUND)
        find_package(Boost REQUIRED)
    endif()
endif()

# Create the Python extension module
pybind11_add_module(boopy boopy.cpp)

# Link Boost headers - handle both old and new Boost installations
if(TARGET Boost::headers)
    target_link_libraries(boopy PRIVATE Boost::headers)
elseif(TARGET Boost::boost)
    target_link_libraries(boopy PRIVATE Boost::boost)
else()
    target_include_directories(boopy PRIVATE ${Boost_INCLUDE_DIRS})
endif()

# Set C++ standard
target_compile_features(boopy PRIVATE cxx_std_14)

# Set visibility
set_target_properties(boopy PROPERTIES CXX_VISIBILITY_PRESET hidden)

# Install the module to the correct location within the package
install(TARGETS boopy LIBRARY DESTINATION resources)