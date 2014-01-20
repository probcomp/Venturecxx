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
import os

#src_dir = "backend/cxx/src"
#src_files = []

#def find_cxx(agg, dirname, fnames):
#    for f in fnames:
#        if f.endswith(".cxx"):
#            agg.append(os.path.join(dirname, f))
#
#os.path.walk(src_dir, find_cxx, src_files)
#print(src_files)

src_files = [
    "src/value.cxx",
    "src/node.cxx",
    "src/env.cxx",
    "src/render.cxx",
    "src/builtin.cxx",
    "src/findsproots.cxx",
    "src/trace.cxx",
    "src/rcs.cxx",
    "src/omegadb.cxx",
    "src/regen.cxx",
    "src/detach.cxx",
    "src/flush.cxx",
    "src/lkernel.cxx",
    "src/infer/gkernel.cxx",
    "src/infer/mh.cxx",
    "src/infer/gibbs.cxx",
    "src/infer/pgibbs.cxx",
    "src/infer/meanfield.cxx",
    "src/utils.cxx",
    "src/check.cxx",
    "src/sp.cxx",
    "src/spaux.cxx",
    "src/scaffold.cxx",
    "src/sps/csp.cxx",
    "src/sps/mem.cxx",
    "src/sps/number.cxx",
    "src/sps/sym.cxx",
    "src/sps/trig.cxx",
    #"src/sps/real.cxx",
    #"src/sps/count.cxx",
    "src/sps/bool.cxx",
    "src/sps/continuous.cxx",
    "src/sps/discrete.cxx",
    "src/sps/cond.cxx",
    "src/sps/vector.cxx",
    "src/sps/list.cxx",
    "src/sps/map.cxx",
    "src/sps/envs.cxx",
    "src/sps/eval.cxx",
    "src/sps/pycrp.cxx",
    "src/sps/makesymdirmult.cxx",
    "src/sps/makedirmult.cxx",
    "src/sps/makebetabernoulli.cxx",
    "src/sps/makeucsymdirmult.cxx",
    "src/sps/makelazyhmm.cxx",
    "src/pytrace.cxx",
]
src_files = ["backend/cxx/" + f for f in src_files]

inc_dirs = ['inc/', 'inc/sps/', 'inc/infer/']
inc_dirs = ["backend/cxx/" + d for d in inc_dirs]

ext_modules = []
packages=["venture","venture.sivm","venture.ripl",
    "venture.parser","venture.server","venture.shortcuts",
    "venture.unit", "venture.test", "venture.cxx", "venture.lite"]

cxx = Extension("venture.cxx.libtrace",
    define_macros = [('MAJOR_VERSION', '0'),
                     ('MINOR_VERSION', '1'),
                     ('REVISION', '1')],
    libraries = ['gsl', 'gslcblas', 'boost_python'],
    extra_compile_args = ["-std=c++11", "-Wall", "-g", "-O0", "-fPIC"],
    undef_macros = ['NDEBUG', '_FORTIFY_SOURCE'],
    include_dirs = inc_dirs,
    sources = src_files)
if "SKIP_CXX_BACKEND" in os.environ:
    print "Skipping CXX backend because SKIP_CXX_BACKEND is %s" % os.environ["SKIP_CXX_BACKEND"]
    print "Unset it to build the CXX backend."
else:
    ext_modules.append(cxx)

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
