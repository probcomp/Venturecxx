# Copyright (c) 2013, MIT Probabilistic Computing Project.
# 
# This file is part of Venture.
# 	
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 	
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 	
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
#!/usr/bin/python

from distutils.core import setup, Extension
from os import path

#src_dir = "backend/cxx/src"
#src_files = []

#def find_cxx(agg, dirname, fnames):
#    for f in fnames:
#        if f.endswith(".cxx"):
#            agg.append(path.join(dirname, f))
#
#path.walk(src_dir, find_cxx, src_files)
#print(src_files)

src_files = [
    "backend/jventure/pytrace.cxx",
]

inc_dirs = ['backend/jventure/','/home/axch/work/pcp/julia/src','/home/axch/work/pcp/julia/src/support','/home/axch/work/pcp/julia/usr/include']

ext_modules = []

packages=["venture","venture.sivm","venture.ripl",
    "venture.parser","venture.server","venture.shortcuts",
    "venture.unit", "venture.test", "venture.cxx", "venture.lite"]

jventure_cxx = Extension("venture.jventure.libtrace",
    define_macros = [('MAJOR_VERSION', '0'),
                     ('MINOR_VERSION', '1'),
                     ('REVISION', '1')],
    libraries = ['boost_python','julia'],
    extra_compile_args = ["-Wall", "-g", "-O0", "-fPIC"],
    undef_macros = ['NDEBUG', '_FORTIFY_SOURCE'],
    include_dirs = inc_dirs,
    library_dirs = ['/home/axch/work/pcp/julia/usr/lib'],
    sources = src_files)

ext_modules.append(jventure_cxx)

setup (
    name = 'Venture CXX',
    version = '0.1.1',
    author = 'MIT.PCP',
    url = 'TBA',
    long_description = 'TBA.',
    packages = packages,
    package_dir={"venture":"python/lib/", "venture.test":"python/test/",
        "venture.cxx":"backend/cxx/", "venture.lite":"backend/lite/"},
    ext_modules = ext_modules,
    scripts = ['script/venture']
)
