CXX=g++
CXXFLAGS=-O3 -march=native -std=c++20 -fopenmp 
LDFLAGS=-fopenmp

.PHONY: all clean

all: main

lcs: main.cpp
	$(CXX) $(CXXFLAGS) $^ -o $@ $(LDFLAGS)

clean:
	rm -f main