src: src.o
	g++ -fopenmp src.o -o src

src.o: src.cpp
	g++ -O3 -fopenmp -mavx512f -c src.cpp -o src.o
