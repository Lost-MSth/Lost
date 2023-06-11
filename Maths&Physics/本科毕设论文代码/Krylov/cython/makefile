PYTHONPATH = "F:/Program Files (x86)/Microsoft Visual Studio/Shared/Python37_64"
INC = $(PYTHONPATH)/include
LIBS = $(PYTHONPATH)/libs
LIB = python37
FILENAME = pauli_func
TMP_DIR = tmp

$(FILENAME).pyd: $(FILENAME).o
	g++ -shared -fopenmp -o $(FILENAME).pyd ./$(TMP_DIR)/$(FILENAME).o -L $(LIBS) -l $(LIB)

$(FILENAME).o: $(FILENAME).cpp
	g++ -DMS_WIN64 -O3 -fopenmp -pthread -fPIC -fwrapv -Wall -o ./$(TMP_DIR)/$(FILENAME).o -c ./$(TMP_DIR)/$(FILENAME).cpp -I $(INC)

$(FILENAME).cpp: $(FILENAME).pyx
	cython -3 --cplus $(FILENAME).pyx -o ./$(TMP_DIR)/$(FILENAME).cpp

.PHONY: clean
clean:
	del *.pyd *.o *.cpp
