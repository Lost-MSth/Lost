.PHONY: all clean bench test_ssyrk test_ssyr2k

CXX = clang++
CXXFLAGS = -O3 -std=c++17 -march=native -fopenmp
INCLUDE_DIR ?= ./OpenBLAS
OpenBLAS ?= ./OpenBLAS/libopenblas.a

all: gen ref test checker

gen: gen.cpp
	$(CXX) $(CXXFLAGS) gen.cpp -o gen

ref: ref.cpp
	$(CXX) $(CXXFLAGS) ref.cpp -o ref

test: test.cpp
	$(CXX) $(CXXFLAGS) -I$(INCLUDE_DIR) test.cpp $(OpenBLAS) -o test

checker: checker.cpp
	$(CXX) $(CXXFLAGS) checker.cpp -o checker

clean:
	rm -f gen ref test checker *.bin

# 测试 SSYRK
test_ssyrk: gen ref test checker
	@echo "========== 测试 SSYRK (N=31, K=2) =========="
	./gen ssyrk 31 2 1.0 0.0 upper notrans 12345 input_ssyrk.bin
	./ref input_ssyrk.bin ref_ssyrk.bin
	OMP_NUM_THREADS=4 ./test input_ssyrk.bin output_ssyrk.bin
	./checker input_ssyrk.bin ref_ssyrk.bin output_ssyrk.bin 1e-4

# 测试 SSYR2K 
test_ssyr2k: gen ref test checker
	@echo "========== 测试 SSYR2K (N=31, K=2) =========="
	./gen ssyr2k 31 2 1.0 0.0 upper notrans 12345 input_ssyr2k.bin
	./ref input_ssyr2k.bin ref_ssyr2k.bin
	OMP_NUM_THREADS=4 ./test input_ssyr2k.bin output_ssyr2k.bin
	./checker input_ssyr2k.bin ref_ssyr2k.bin output_ssyr2k.bin 1e-4

# 大规模性能测试
bench: gen test
	@echo "========== 性能测试 SSYRK (N=20000, K=4096) =========="
	./gen ssyrk 20000 4096 1.0 0.0 upper notrans 12345 input_large_ssyrk.bin
	./ref input_large_ssyrk.bin ref_large_ssyrk.bin
	OMP_NUM_THREADS=4 ./test input_large_ssyrk.bin output_large_ssyrk.bin
	./checker input_large_ssyrk.bin ref_large_ssyrk.bin output_large_ssyrk.bin
	@echo ""
	@echo "========== 性能测试 SSYR2K (N=20000, K=4096) =========="
	./gen ssyr2k 20000 4096 1.0 0.0 upper notrans 12345 input_large_ssyr2k.bin
	./ref input_large_ssyr2k.bin ref_large_ssyr2k.bin
	OMP_NUM_THREADS=4 ./test input_large_ssyr2k.bin output_large_ssyr2k.bin
	./checker input_large_ssyr2k.bin ref_large_ssyr2k.bin output_large_ssyr2k.bin

