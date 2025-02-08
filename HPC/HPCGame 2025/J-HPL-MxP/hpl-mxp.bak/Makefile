CC = gcc
CFLAGS = 
LDFLAGS =

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