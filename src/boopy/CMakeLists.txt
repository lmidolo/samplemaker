cmake_minimum_required(VERSION 3.18)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(POLICY CMP0167)
  cmake_policy(SET CMP0167 NEW)
endif()

project(boopy LANGUAGES C CXX)
set(X_VCPKG_APPLOCAL_DEPS_INSTALL ON)

find_package(Boost REQUIRED COMPONENTS polygon)

add_library(boopy_ffi SHARED boopy_ffi.cpp boopy_ffi.h)


target_link_libraries(boopy_ffi PRIVATE Boost::polygon)
set_target_properties(boopy_ffi PROPERTIES PUBLIC_HEADER boopy_ffi.h)
install(TARGETS boopy_ffi)