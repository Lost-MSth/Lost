.PHONY: clean bench

CFLAGS = -O3 -std=c++20 -flto -march=native -fopenmp -pthread

seed=42

exe=./sssp.exe
end=.out

all: sssp

sssp: sssp.o main.o
	g++ $(CFLAGS) sssp.o main.o -o sssp

%.o: %.cpp
	g++ $(CFLAGS) -c $< -o $@

clean:
	rm -rf *.o sssp

bench: sssp
	OMP_NUM_THREADS=16 OMP_PLACES=cores OMP_PROC_BIND=close $(exe) 100000 200000 ${seed} 1$(end)
	OMP_NUM_THREADS=16 OMP_PLACES=cores OMP_PROC_BIND=close $(exe) 100000 10000000 ${seed} 2$(end)
	OMP_NUM_THREADS=16 OMP_PLACES=cores OMP_PROC_BIND=close $(exe) 1000000 200000000 ${seed} 3$(end)
	OMP_NUM_THREADS=16 OMP_PLACES=cores OMP_PROC_BIND=close $(exe) 1000000 100000000 ${seed} 4$(end)
	OMP_NUM_THREADS=16 OMP_PLACES=cores OMP_PROC_BIND=close $(exe) 10000000 10000000 ${seed} 5$(end)
	OMP_NUM_THREADS=16 OMP_PLACES=cores OMP_PROC_BIND=close $(exe) 10000000 20000000 ${seed} 6$(end)
	OMP_NUM_THREADS=16 OMP_PLACES=cores OMP_PROC_BIND=close $(exe) 10000000 100000000 ${seed} 7$(end)