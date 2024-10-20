PYTHONPATH = "F:/Program Files/Python/Python312"
INC = $(PYTHONPATH)/include
LIBS = $(PYTHONPATH)/libs
LIB = python312
FILENAME = gorand

$(FILENAME).pyd: $(FILENAME).o
	gcc -shared -o $(FILENAME).pyd $(FILENAME).o -L $(LIBS) -l $(LIB)

$(FILENAME).o: $(FILENAME).c
	gcc -DMS_WIN64 -O3 -pthread -fPIC -fwrapv -Wall -o $(FILENAME).o -c $(FILENAME).c -I $(INC)

$(FILENAME).c: $(FILENAME).pyx
	cython -3 $(FILENAME).pyx -o $(FILENAME).c

.PHONY: clean
clean:
	del *.pyd *.o *.c
