src: src.o
	g++ -fopenmp src.o -o src

src.o: src.cpp
	g++ -O3 -fopenmp -march=native -ffast-math -std=c++20 -c src.cpp -o src.o
