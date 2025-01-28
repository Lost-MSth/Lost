import numpy
n1=512
n2=512
x=numpy.zeros(2+n1*n2,dtype=numpy.int32)
x[0]=n1
x[1]=n2
r=numpy.random.rand(n1*n2)
x[2:][r>0.1]=1
x[2:][r>0.4]=2
x[2:][r>0.7]=3
x.tofile('in.data')
