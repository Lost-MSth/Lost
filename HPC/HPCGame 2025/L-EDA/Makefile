CXX = g++
CFLAGS = -O3 -fopenmp
LIBS = -fopenmp

.PHONY: all clean

all: flute datagen

flute: flute.cpp
	$(CXX) $(CFLAGS) -o $@ $< $(LIBS)

datagen: datagen.cpp
	$(CXX) $(CFLAGS) -o $@ $< $(LIBS)

clean:
	rm -f flute datagen