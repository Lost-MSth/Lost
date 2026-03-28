CC = g++
CFLAGS = -O3 -fopenmp -mavx512f
LDFLAGS = -O3 -fopenmp -mavx512f

# 默认目标
all: solver match-baseline generator

solver: solver.cpp
	$(CC) $(CFLAGS) -o solver solver.cpp $(LDFLAGS)

match-baseline: match-baseline.cpp
	$(CC) $(CFLAGS) -o match-baseline match-baseline.cpp $(LDFLAGS)

generator: generator.cpp
	$(CC) $(CFLAGS) -o generator generator.cpp $(LDFLAGS)

clean:
	rm -f solver solver.o match-baseline match-baseline.o generator generator.o

# 测试 baseline
test_baseline: match-baseline
	@echo "========== BASELINE =========="
	OMP_NUM_THREADS=32 ./match-baseline text.bin patterns.bin output_baseline.bin
	hexdump -C output_baseline.bin

# 测试 solver 
test: solver
	@echo "========== SOLVER =========="
	OMP_NUM_THREADS=32 ./solver text.bin patterns.bin output_solver.bin
# 	@echo "========== 比较结果 =========="
# 	diff output_baseline.bin output_solver.bin && echo "结果一致！" || echo "结果不一致！"
	hexdump -C output_solver.bin

.PHONY: all data clean test test_baseline generator