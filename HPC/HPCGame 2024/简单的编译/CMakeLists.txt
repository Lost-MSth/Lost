# FILEPATH: /C:/Users/Lost/Desktop/hpcgame 2024/简单的编译/CMakeLists.txt

cmake_minimum_required(VERSION 3.12)
project(hpcgame)
enable_language(CUDA)


find_package(OpenMP REQUIRED)

find_package(MPI REQUIRED)

find_package(CUDA REQUIRED)

add_executable(hello_omp hello_omp.cpp)
target_link_libraries(hello_omp PRIVATE OpenMP::OpenMP_CXX)


add_executable(hello_mpi hello_mpi.cpp)
target_link_libraries(hello_mpi PRIVATE MPI::MPI_CXX)


include_directories(${CUDA_INCLUDE_DIRS})
add_executable(hello_cuda hello_cuda.cu)
target_link_libraries(hello_cuda ${CUDA_LIBRARIES})
