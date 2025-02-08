CC = clang
CFLAGS = -O3 -mcpu=hip09 -I$(INCLUDE) -I$(CPATH)
LDFLAGS = -L$(LD_LIBRARY_PATH) -lkblas

.PHONY: all clean

all: hpl-ai

# hpl-ai.o 是预编译的
hpl-ai: blas.o gmres.o sgetrf_nopiv.o 
	$(CC) $(CFLAGS) hpl-ai.o $^ -o $@ -lm $(LDFLAGS)

# Pattern rule
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@ 

clean:
	rm -f hpl-ai blas.o gmres.o sgetrf_nopiv.o