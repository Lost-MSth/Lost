import numpy
x=numpy.fromfile('in.data',dtype=numpy.int32)
n1=x[0]
n2=x[1]
m=x[2:].reshape((n2,n1))
im=numpy.zeros((n2,n1),dtype=numpy.int32)

ci=0
for i in range(n2):
    for j in range(n1):
        if m[i,j]:
            im[i,j]=ci
            ci+=1
        else:
            im[i,j]=-1
nl=((0,1),(0,-1),(1,0),(-1,0),(0,0))

import sage.all
t=sage.all.Integers(3)

a=sage.all.matrix(t,ci,ci)
y=sage.all.vector(t,ci)
for i in range(n2):
    for j in range(n1):
        ci=im[i,j]
        if ci>=0:
            y[ci]=3-m[i,j]
            for nl_ in nl:
                i_=i+nl_[0]
                j_=j+nl_[1]
                if 0<=i_ and i_<n2 and 0<=j_ and j_<n1:
                    ci_=im[i_,j_]
                    if ci_>=0:
                        a[ci_,ci]=1

x_t=a.solve_right(y)

x=numpy.zeros((n2,n1),dtype=numpy.int32)
for i in range(n2):
    for j in range(n1):
        ci=im[i,j]
        if ci>=0:
            x[i,j]=x_t[ci]
x.tofile('out.data')