cmake_minimum_required(VERSION 3.4...3.18)
project(example LANGUAGES CXX)

find_package(pybind11 REQUIRED)
pybind11_add_module(example main.cpp)