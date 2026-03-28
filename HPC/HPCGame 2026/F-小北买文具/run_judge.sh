#!/bin/bash

# LU Solver Competition Judging Script
# 设置环境变量
export OMP_NUM_THREADS=16
export OMP_PROC_BIND=close
export OMP_PLACES=cores

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "LU Solver Competition Judge System"
echo "========================================="
echo "Environment:"
echo "  OMP_NUM_THREADS: $OMP_NUM_THREADS"
echo "  CPU: $(lscpu | grep 'Model name' | cut -d: -f2 | xargs)"
echo "========================================="
echo ""

# 检查必要文件
if [ ! -f "solver.cpp" ]; then
    echo -e "${RED}Error: solver.cpp not found!${NC}"
    exit 1
fi

if [ ! -f "driver.cpp" ]; then
    echo -e "${RED}Error: driver.cpp not found!${NC}"
    exit 1
fi

# 编译
echo "Compiling..."
# make clean > /dev/null 2>&1
make checker
make solver 2>&1 | grep -i "error"
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo -e "${RED}Compilation failed!${NC}"
    exit 1
fi
echo -e "${GREEN}Compilation successful!${NC}"
echo ""

# 生成测试数据
# echo "Generating test data..."
# make data > /dev/null 2>&1
# if [ $? -ne 0 ]; then
#     echo -e "${RED}Failed to generate test data!${NC}"
#     exit 1
# fi
# echo -e "${GREEN}Test data generated!${NC}"
# echo ""

score=0
total_time=0

# 函数：运行单个测试点
run_test() {
    local N=$1
    local TL=$2
    local POINTS=$3
    local TEST_NUM=$4
    
    echo "----------------------------------------"
    echo "Test #$TEST_NUM: N=$N (Time Limit: ${TL}s, Points: $POINTS)"
    echo "----------------------------------------"
    
    # 检查输入文件是否存在
    if [ ! -f "input_${N}.bin" ]; then
        echo -e "${RED}Input file input_${N}.bin not found!${NC}"
        return
    fi
    
    # 运行选手程序
    start=$(date +%s.%N)
    timeout $TL ./solver input_${N}.bin output.bin > solver_output.txt 2>&1
    ret=$?
    end=$(date +%s.%N)
    runtime=$(echo "scale=6; ($end - $start)/1" | bc | sed 's/^\./0./')
    
    # 提取性能信息
    if [ -f solver_output.txt ]; then
        gflops=$(grep "GFLOPS" solver_output.txt | awk '{print $2}')
    fi
    
    # 检查超时
    if [ $ret -eq 124 ]; then
        echo -e "${RED}Time Limit Exceeded!${NC} (>${TL}s)"
        echo "Score: 0/$POINTS"
        return
    fi
    
    # 检查运行时错误
    if [ $ret -ne 0 ]; then
        echo -e "${RED}Runtime Error!${NC} (exit code: $ret)"
        echo "Score: 0/$POINTS"
        return
    fi
    
    # 检查输出文件
    if [ ! -f output.bin ]; then
        echo -e "${RED}Output file not found!${NC}"
        echo "Score: 0/$POINTS"
        return
    fi
    
    # 检查正确性
    ./checker input_${N}.bin output.bin > checker_output.txt 2>&1
    checker_ret=$?
    
    if [ $checker_ret -eq 0 ]; then
        # 提取相对误差
        rel_error=$(grep "Relative Error" checker_output.txt | awk '{print $4}')
        echo -e "${GREEN}✓ PASSED${NC}"
        echo "  Time: ${runtime}s"
        if [ ! -z "$gflops" ]; then
            echo "  Performance: ${gflops} GFLOPS"
        fi
        echo "  Relative Error: ${rel_error}"
        echo "  Score: +${POINTS} pts"
        score=$((score + POINTS))
        total_time=$(echo "$total_time + $runtime" | bc)
    else
        # 提取错误信息
        rel_error=$(grep "Relative Error" checker_output.txt | awk '{print $4}')
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Relative Error: ${rel_error} (threshold: 1e-5)"
        echo "  Score: 0/$POINTS"
    fi
    
    # 清理临时文件
    # rm -f solver_output.txt checker_output.txt output.bin
}

# 执行测试点（与 statement.md 一致）
run_test 2049 0.14  20  3
run_test 4096 1.6  20  3
run_test 8192 10  20  4
run_test 16384 72  20  5
run_test 32768 500 20 3
# run_test 2049 0.07  20  3
# run_test 4096 0.8  20  3
# run_test 8192 5.3  20  4
# run_test 16384 36.5  20  5
# run_test 32768 268 20 3

echo ""
echo "========================================="
echo "Final Results"
echo "========================================="
echo "Total Score: $score / 100"
echo "Total Time: ${total_time}s"
echo "========================================="

exit 0
