PYTHONPATH = "F:/Program Files (x86)/Microsoft Visual Studio/Shared/Python37_64"
INC = $(PYTHONPATH)/include
LIBS = $(PYTHONPATH)/libs
LIB = python37
NUMPY = $(PYTHONPATH)/lib/site-packages/numpy/core/include
FILENAME = utils
TMP_DIR = tmp

$(FILENAME).pyd: $(FILENAME).o
	gcc -shared -o $(FILENAME).pyd ./$(TMP_DIR)/$(FILENAME).o -L $(LIBS) -l $(LIB)

$(FILENAME).o: $(FILENAME).c
	gcc -DMS_WIN64 -O3 -pthread -fPIC -fwrapv -Wall -o ./$(TMP_DIR)/$(FILENAME).o -c ./$(TMP_DIR)/$(FILENAME).c -I $(INC) -I $(NUMPY)

$(FILENAME).c: $(FILENAME).pyx
	cython -3 $(FILENAME).pyx -o ./$(TMP_DIR)/$(FILENAME).c

.PHONY: clean
clean:
	del *.pyd *.o *.c
