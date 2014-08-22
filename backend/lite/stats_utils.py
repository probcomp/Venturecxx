import sys
from cffi import FFI
from os.path import expanduser

if not 'ffi' in locals():
  ffi = FFI()
  ffi.cdef("""
    double gammaln(double x);
    double student_cdf(int df, double t);
    void print_array(double *x, int N, double *y);
    """)
  C = ffi.dlopen(expanduser('~') + '/lib/libutil.so')

