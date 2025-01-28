CXX = g++
CFLAGS = -O3 -march=native
LIBS = -lsecp256k1 -lcrypto

.PHONY: all clean

all: vanity chk

vanity: vanity.cpp
	$(CXX) $(CFLAGS) -o $@ $< $(LIBS)

chk: chk.cpp
	$(CXX) $(CFLAGS) -o $@ $< $(LIBS)

clean:
	rm -f vanity chk