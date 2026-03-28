cmake_minimum_required(VERSION 3.14)
project(mr_spgemm_topk LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(MPI REQUIRED)

add_executable(mr_spgemm_topk
	src/main.cpp
	src/spgemm.cpp
)

target_link_libraries(mr_spgemm_topk PRIVATE MPI::MPI_CXX)
target_compile_options(mr_spgemm_topk PRIVATE -O3 -march=native -Wall -Wextra -Wpedantic)
