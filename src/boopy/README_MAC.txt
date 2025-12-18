Boopy should be compiled separately on MACOS, if it doesn't work by default.


Get the latest release from https://www.boost.org/releases/latest/ and choose the Unix version.
To unzip, run:
# tar -xvf boost_1_xx_y.tar.gz 

Go to the src/boopy subfolder and compile using clang++

# clang++ -fPIC -o boopy_ffi.o -c boopy_ffi.cpp -I<path_to_boost>
# clang++ -shared -o libboopy_ffi_mac.so boopy_ffi.o

Then copy the file libboopy_ffi_mac.so into src/samplemaker/resources

Contact the repo maintainer if you encounter any issues.

