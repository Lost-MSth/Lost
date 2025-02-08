# Set the Intel compilers
set(CMAKE_C_COMPILER icx)
set(CMAKE_CXX_COMPILER icpx)

cmake_minimum_required(VERSION 3.20)

project(FilterProject LANGUAGES C CXX)

# O3 & AVX512
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fast")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fast")

add_executable(program main.cpp filter.F90)
target_link_libraries(program stdc++)
set_source_files_properties(filter.F90 PROPERTIES LANGUAGE C)
