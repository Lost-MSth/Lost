#!/usr/bin/bash

module load bisheng/compiler4.1.0/bishengmodule
module load bisheng/kml2.5.0/kml
# module load gcc/compiler12.3.1/gccmodule
# module load gcc/kml2.5.0/kml

module list

echo $LD_LIBRARY_PATH
export LIBRARY_PATH=$LD_LIBRARY_PATH

# which clang

echo "=============Compiling HPL-AI============="

make -j

./hpl-ai