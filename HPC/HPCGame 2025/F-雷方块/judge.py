import numpy
x=numpy.fromfile('in.data',dtype=numpy.int32)
n1=x[0]
n2=x[1]
m=x[2:].reshape((n2,n1))

m_=numpy.fromfile('out.data',dtype=numpy.int32).reshape((n2,n1))
assert((m_<=2).all()) # 敲3次等于没敲
assert((m_>=0).all()) # 怎么想都不能敲-1次
m__=numpy.array(m_)
m__[:,1:]+=m_[:,:-1]
m__[:,:-1]+=m_[:,1:]
m__[1:,:]+=m_[:-1,:]
m__[:-1,:]+=m_[1:,:]
assert(((m+m__)%3*m==0).all()) # 所有方块状态为3
assert(((m==0)*m_==0).all())   # 没有方块的位置必须是0

print('ok')
