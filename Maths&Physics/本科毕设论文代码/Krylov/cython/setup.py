from distutils.core import setup

from Cython.Build import cythonize

# openmp别忘了
setup(
    ext_modules=cythonize("./pauli_func.pyx", extra_compile_args=['-O3', '-fopenmp'], language="c++"),
)
