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
import sys

#src_dir = "backend/cxx/src"
#src_files = []

#def find_cxx(agg, dirname, fnames):
#    for f in fnames:
#        if f.endswith(".cxx"):
#            agg.append(os.path.join(dirname, f))
#
#os.path.walk(src_dir, find_cxx, src_files)
#print(src_files)

ON_LINUX = 'linux' in sys.platform
if ON_LINUX:
    os.environ['CC'] = 'ccache gcc'

src_files = [
    "src/args.cxx",
    "src/builtin.cxx",

    "src/concrete_trace.cxx",
    "src/consistency.cxx",
        
    "src/db.cxx",
    "src/detach.cxx",            

    "src/env.cxx",
    "src/expressions.cxx",    

    "src/gkernel.cxx",
    
    "src/indexer.cxx",
    "src/lkernel.cxx",
    "src/mixmh.cxx",
    "src/node.cxx",
    "src/particle.cxx",
    "src/psp.cxx",
    "src/pytrace.cxx",
    "src/pyutils.cxx",
    "src/regen.cxx",
    "src/scaffold.cxx",
    "src/sp.cxx",
    "src/trace.cxx",
    "src/utils.cxx",
    "src/value.cxx",
    "src/values.cxx",

    "src/gkernels/mh.cxx",
    "src/gkernels/pgibbs.cxx",

    "src/sps/conditional.cxx",
    "src/sps/continuous.cxx",
    "src/sps/csp.cxx",
    "src/sps/deterministic.cxx",
    "src/sps/dir_mult.cxx",
    "src/sps/discrete.cxx",
    "src/sps/dstructure.cxx",
    "src/sps/eval.cxx",
    "src/sps/hmm.cxx",
    "src/sps/matrix.cxx",    
    "src/sps/msp.cxx",
    "src/sps/scope.cxx",    
]
src_files = ["backend/new_cxx/" + f for f in src_files]

inc_dirs = ['inc/', 'inc/sps/', 'inc/infer/', 'inc/Eigen']
inc_dirs = ["backend/new_cxx/" + d for d in inc_dirs]

ext_modules = []
packages=["venture","venture.sivm","venture.ripl",
          "venture.parser","venture.server","venture.shortcuts",
          "venture.unit", "venture.test", "venture.cxx", "venture.lite",
          "venture.venturemagics"]

cxx = Extension("venture.cxx.libtrace",
    define_macros = [('MAJOR_VERSION', '0'),
                     ('MINOR_VERSION', '1'),
                     ('REVISION', '1')],
    libraries = ['gsl', 'gslcblas', 'boost_python', 'boost_system'],
    extra_compile_args = ["-Wall", "-g", "-O0", "-fPIC"],
    #undef_macros = ['NDEBUG', '_FORTIFY_SOURCE'],
    include_dirs = inc_dirs,
    sources = src_files)

if "SKIP_CXX_BACKEND" in os.environ:
    print "Skipping CXX backend because SKIP_CXX_BACKEND is %s" % os.environ["SKIP_CXX_BACKEND"]
    print "Unset it to build the CXX backend."
else:
    ext_modules.append(cxx)

# monkey-patch for parallel compilation from
# http://stackoverflow.com/questions/11013851/speeding-up-build-process-with-distutils
def parallelCCompile(self, sources, output_dir=None, macros=None, include_dirs=None,
                     debug=0, extra_preargs=None, extra_postargs=None, depends=None):
    # those lines are copied from distutils.ccompiler.CCompiler directly
    macros, objects, extra_postargs, pp_opts, build = self._setup_compile(output_dir, macros, include_dirs, sources, depends, extra_postargs)
    cc_args = self._get_cc_args(pp_opts, debug, extra_preargs)
    
    # FIXME: this is probably not the best way to do this
    # I could find no other way to override the extra flags
    # from the python makefile's CFLAGS and OPTS variables
    self.compiler_so = ["ccache", "gcc"]
    
    # parallel code
    N=2 # number of parallel compilations
    import multiprocessing.pool
    def _single_compile(obj):
        try: src, ext = build[obj]
        except KeyError: return
        self._compile(obj, src, ext, cc_args, extra_postargs, pp_opts)
    # convert to list, imap is evaluated on-demand
    list(multiprocessing.pool.ThreadPool(N).imap(_single_compile,objects))
    return objects
import distutils.ccompiler
distutils.ccompiler.CCompiler.compile=parallelCCompile

setup (
    name = 'Venture CXX',
    version = '0.1.1',
    author = 'MIT.PCP',
    url = 'TBA',
    long_description = 'TBA.',
    packages = packages,
    package_dir={"venture":"python/lib/", "venture.test":"test/",
        "venture.cxx":"backend/new_cxx/", "venture.lite":"backend/lite/"},
    ext_modules = ext_modules,
    scripts = ['script/venture']
)
