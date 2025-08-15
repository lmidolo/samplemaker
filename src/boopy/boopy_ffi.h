/******************************************************************************
 * This file is part of sample_maker
 *
 *  
 ******************************************************************************/

#ifndef BOOPY_FFI_H
#define BOOPY_FFI_H

/**
 * @brief FFI library for boost - polygon
 *
 * This wrapper is intended for running polygon functions in sample_maker
 * using the Boost Polygon library.
 *
 */
 
#ifdef WIN32
#define DLL_EXPORT extern "C" __declspec(dllexport)
#elif __APPLE__
#define DLL_EXPORT                                                             \
  extern "C" __attribute__((visibility("default"))) __attribute__((used))
#else
#define DLL_EXPORT
#endif

DLL_EXPORT void bp_setGroupAddress(const unsigned int addr);

DLL_EXPORT void bp_addPolyData(const int* data, unsigned int size);

DLL_EXPORT unsigned int bp_getPolyCount(void);

DLL_EXPORT unsigned int bp_getPolySize(unsigned int n);

DLL_EXPORT void bp_getPoly(int *data, unsigned int size, unsigned int n);

DLL_EXPORT double bp_area(void);

DLL_EXPORT void bp_clear(void);

DLL_EXPORT bool bp_empty(void);

DLL_EXPORT void bp_difference(unsigned int addr);

DLL_EXPORT void bp_intersection(unsigned int addr);

DLL_EXPORT void bp_merge(unsigned int addr);

DLL_EXPORT void bp_assign(void);

DLL_EXPORT void bp_exor(unsigned int addr);

DLL_EXPORT void bp_trapezoids(void);

DLL_EXPORT void bp_resize(double value, bool corner_fill_arc, unsigned int num_circle_segments);


#endif // BOOPY_FFI_H