ALL: hello_omp hello_cuda hello_mpi

hello_omp: hello_omp.o
	g++ -fopenmp hello_omp.o -o hello_omp

hello_omp.o: hello_omp.cpp
	g++ -fopenmp -c hello_omp.cpp -o hello_omp.o

hello_mpi: hello_mpi.o
	mpic++ hello_mpi.o -o hello_mpi

hello_mpi.o: hello_mpi.cpp
	mpic++ -c hello_mpi.cpp -o hello_mpi.o

hello_cuda: hello_cuda.o
	nvcc hello_cuda.o -o hello_cuda

hello_cuda.o: hello_cuda.cu
	nvcc -c hello_cuda.cu -o hello_cuda.o
