# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.
#!/usr/bin/env python

from distutils.core import setup, Extension
import os
import sys

with open('VERSION', 'rU') as f:
    version = f.readline().strip()

# Append the Git commit id if this is a development version.
if version.endswith('+'):
    prefix = 'release-'
    tag = prefix + version[:-1]
    try:
        import subprocess
        # The --tags option includes non-annotated tags in the search.
        desc = subprocess.check_output([
            'git', 'describe', '--dirty', '--match', tag, '--tags'
        ])
    except Exception:
        version += 'unknown'
    else:
        assert desc.startswith(tag)
        version = desc[len(prefix):].strip()

# XXX Mega-kludge.  See below about grammars for details.
try:
    with open('python/lib/version.py', 'rU') as f:
        version_old = f.readlines()
except IOError:
    version_old = None
version_new = ['__version__ = %s\n' % (repr(version),)]
if version_old != version_new:
    with open('python/lib/version.py', 'w') as f:
        f.writelines(version_new)

ON_LINUX = 'linux' in sys.platform
ON_MAC = 'darwin' in sys.platform

cflags = os.getenv("CFLAGS", "").split()

if ON_LINUX:
    os.environ['CC'] = 'ccache gcc '
if ON_MAC:
    os.environ['CC'] = 'ccache gcc'
    os.environ['CXX'] = 'ccache g++'
    os.environ['CFLAGS'] = "-std=c++11 -stdlib=libc++"

puma_src_files = [
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
    "src/serialize.cxx",
    "src/sp.cxx",
    "src/sprecord.cxx",
    "src/stop_and_copy.cxx",
    "src/trace.cxx",
    "src/utils.cxx",
    "src/value.cxx",
    "src/values.cxx",

    "src/gkernels/func_mh.cxx",
    "src/gkernels/mh.cxx",
    "src/gkernels/rejection.cxx",
    "src/gkernels/pgibbs.cxx",
    "src/gkernels/egibbs.cxx",
    "src/gkernels/slice.cxx",
    "src/gkernels/hmc.cxx",

    "src/sps/betabernoulli.cxx",
    "src/sps/conditional.cxx",
    "src/sps/continuous.cxx",
    "src/sps/crp.cxx",
    "src/sps/csp.cxx",
    "src/sps/deterministic.cxx",
    "src/sps/dir_mult.cxx",
    "src/sps/discrete.cxx",
    "src/sps/dstructure.cxx",
    "src/sps/eval.cxx",
    "src/sps/hmm.cxx",
    "src/sps/lite.cxx",
    "src/sps/matrix.cxx",
    "src/sps/misc.cxx",
    "src/sps/msp.cxx",
    "src/sps/mvn.cxx",
    "src/sps/silva_mvn.cxx",
    "src/sps/numerical_helpers.cxx",
    "src/sps/scope.cxx",
]
puma_src_files = ["backend/new_cxx/" + f for f in puma_src_files]

puma_inc_dirs = ['inc/', 'inc/sps/', 'inc/infer/']
puma_inc_dirs = ["backend/new_cxx/" + d for d in puma_inc_dirs]

ext_modules = []
packages = [
    "venture",
    "venture.engine",
    "venture.lite",
    "venture.lite.infer",
    "venture.untraced",
    "venture.parser",
    "venture.parser.church_prime",
    "venture.parser.venture_script",
    "venture.plex",
    "venture.puma",
    "venture.ripl",
    "venture.server",
    "venture.shortcuts",
    "venture.sivm",
    "venture.test",
    "venture.unit",
    "venture.value",
    "venture.venturemagics",
]

if ON_LINUX:
    puma = Extension("venture.puma.libpumatrace",
        define_macros = [('MAJOR_VERSION', '0'),
                         ('MINOR_VERSION', '1'),
                         ('REVISION', '1')],
        libraries = ['gsl', 'gslcblas', 'boost_python', 'boost_system', 'boost_thread'],
        extra_compile_args = ["-Wall", "-g", "-O2", "-fPIC", "-fno-omit-frame-pointer"] + cflags,
        #undef_macros = ['NDEBUG', '_FORTIFY_SOURCE'],
        include_dirs = puma_inc_dirs,
        sources = puma_src_files)
if ON_MAC:
    puma = Extension("venture.puma.libpumatrace",
        define_macros = [('MAJOR_VERSION', '0'),
                         ('MINOR_VERSION', '1'),
                         ('REVISION', '1')],
        libraries = ['gsl', 'gslcblas', 'boost_python-mt', 'boost_system-mt', 'boost_thread-mt'],
        extra_compile_args = ["-Wall", "-g", "-O2", "-fPIC", "-fno-omit-frame-pointer"] + cflags,
        #undef_macros = ['NDEBUG', '_FORTIFY_SOURCE'],
        include_dirs = puma_inc_dirs,
        sources = puma_src_files)

if "SKIP_PUMA_BACKEND" in os.environ:
    print "Skipping Puma backend because SKIP_PUMA_BACKEND is %s" % os.environ["SKIP_PUMA_BACKEND"]
    print "Unset it to build the Puma backend."
else:
    ext_modules.append(puma)

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
    if ON_LINUX:
        self.compiler_so = ["ccache", "gcc"]
    if ON_MAC:
        self.compiler_so = ["ccache", "gcc"]

    # parallel code
    import multiprocessing, multiprocessing.pool
    N=multiprocessing.cpu_count() # number of parallel compilations
    def _single_compile(obj):
        try: src, ext = build[obj]
        except KeyError: return
        self._compile(obj, src, ext, cc_args, extra_postargs, pp_opts)
    # convert to list, imap is evaluated on-demand
    list(multiprocessing.pool.ThreadPool(N).imap(_single_compile,objects))
    return objects
import distutils.ccompiler
distutils.ccompiler.CCompiler.compile=parallelCCompile

# XXX This is a mega-kludge.  Since distutils/setuptools has no way to
# order dependencies (what kind of brain-dead build system can't do
# this?), we just always regenerate the grammar.  Could hack
# distutils.command.build to include a dependency mechanism, but this
# is more expedient for now.
grammars = [
    'python/lib/parser/church_prime/grammar.y',
    'python/lib/parser/venture_script/grammar.y',
]

import distutils.spawn
import errno
import os
import os.path
root = os.path.dirname(os.path.abspath(__file__))
lemonade = root + '/external/lemonade/dist'
for grammar in grammars:
    parser = os.path.splitext(grammar)[0] + '.py'
    parser_mtime = None
    try:
        parser_mtime = os.path.getmtime(parser)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise
    if parser_mtime is not None:
        if os.path.getmtime(grammar) < parser_mtime:
            continue
    print 'generating %s -> %s' % (grammar, parser)
    distutils.spawn.spawn([
        '/usr/bin/env', 'PYTHONPATH=' + lemonade,
        lemonade + '/bin/lemonade',
        '-s',                   # Write statistics to stdout.
        grammar,
    ])

setup (
    name = 'Venture CXX',
    version = version,
    author = 'MIT.PCP',
    url = 'TBA',
    long_description = 'TBA.',
    packages = packages,
    package_dir = {
        "venture": "python/lib/",
        "venture.lite": "backend/lite/",
        "venture.untraced": "backend/untraced/",
        "venture.plex": "external/plex/dist/Plex/",
        "venture.puma": "backend/new_cxx/",
        "venture.test": "test/",
    },
    package_data = {'':['*.vnt']},
    ext_modules = ext_modules,
    scripts = ['script/venture', 'script/vendoc']
)
