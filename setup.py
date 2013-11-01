#!/usr/bin/python

# From here:
# http://docs.python.org/2/extending/building.html#building

# Just build as a Python library: python setup.py build
# Build and install to the system: sudo python setup.py build install

from distutils.core import setup, Extension
import os
import itertools

source_dirs = ["backend/cxx/src/", "backend/cxx/src/sps/"]
source_files = list(itertools.chain(*[[d + f for f in os.listdir(d) if f.endswith(".cxx")] for d in source_dirs]))
#print(source_files)

ext_modules = []
packages=["venture","venture.sivm","venture.ripl",
    "venture.parser","venture.server","venture.shortcuts",
    "venture.test", "venture.cxx"]

cxx = Extension("venture.cxx.libtrace",
    define_macros = [('MAJOR_VERSION', '1'),
                     ('MINOR_VERSION', '0')],
    libraries = ['gsl', 'gslcblas', 'boost_python'],
    extra_compile_args = ["-std=c++11", "-Wall", "-g", "-O2", "-fPIC"],
    include_dirs = ["backend/cxx/inc/", "backend/cxx/inc/sps/"],
    sources = source_files)
ext_modules.append(cxx)

setup (
    name = 'Venture CXX',
    version = '1.0',
    author = 'MIT.PCP',
    url = 'TBA',
    long_description = 'TBA.',
    packages = packages,
    package_dir={"venture":"python/lib/", "venture.test":"python/test/", "venture.cxx":"backend/cxx/"},
    ext_modules = ext_modules
)
