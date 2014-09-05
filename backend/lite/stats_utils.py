import sys
from cffi import FFI
from os.path import expanduser

if not 'ffi' in locals():
  ffi = FFI()
  ffi.cdef("""
    double gammaln(double x);
    double student_cdf(int df, double t);
    """)
  C = ffi.dlopen(expanduser('~') + '/lib/pypy_lib.so')

