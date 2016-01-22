# Copyright (c) 2013, 2014, 2015, 2016 MIT Probabilistic Computing Project.
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

try:
    from setuptools import setup, Extension
    from setuptools.command.build_py import build_py
    from setuptools.command.sdist import sdist
except ImportError:
    from distutils.core import setup, Extension
    from distutils.command.build_py import build_py
    from distutils.command.sdist import sdist

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
        import re
        match = re.match(prefix + r'([^-]*)-([0-9]+)-(.*)$', desc)
        if match is None:       # paranoia
            version += 'unknown'
        else:
            ver, rev, local = match.groups()
            version = '%s.post%s+%s' % (ver, rev, local.replace('-', '.'))
            assert '-' not in version

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
    "venture.plugins",
    "venture.puma",
    "venture.ripl",
    "venture.server",
    "venture.shortcuts",
    "venture.sivm",
    "venture.test",
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

lemonade = 'external/lemonade/dist'
grammars = [
    'python/lib/parser/church_prime/grammar.y',
    'python/lib/parser/venture_script/grammar.y',
]

def sha256_file(pathname):
    import hashlib
    sha256 = hashlib.sha256()
    with open(pathname, 'rb') as source_file:
        for block in iter(lambda: source_file.read(65536), ''):
            sha256.update(block)
    return sha256

def uptodate(path_in, path_out, path_sha256):
    import errno
    try:
        with open(path_sha256, 'rb') as file_sha256:
            # Strip newlines and compare.
            if file_sha256.next()[:-1] != sha256_file(path_in).hexdigest():
                return False
            if file_sha256.next()[:-1] != sha256_file(path_out).hexdigest():
                return False
    except (IOError, OSError) as e:
        if e.errno != errno.ENOENT:
            raise
        return False
    return True

def commit(path_in, path_out, path_sha256):
    with open(path_sha256 + '.tmp', 'wb') as file_sha256:
        file_sha256.write('%s\n' % (sha256_file(path_in).hexdigest(),))
        file_sha256.write('%s\n' % (sha256_file(path_out).hexdigest(),))
    os.rename(path_sha256 + '.tmp', path_sha256)

def generate_parser(lemonade, path_y):
    import distutils.spawn
    root = os.path.dirname(os.path.abspath(__file__))
    lemonade = os.path.join(root, *lemonade.split('/'))
    base, ext = os.path.splitext(path_y)
    assert ext == '.y'
    path_py = base + '.py'
    path_sha256 = base + '.sha256'
    if uptodate(path_y, path_py, path_sha256):
        return
    print 'generating %s -> %s' % (path_y, path_py)
    distutils.spawn.spawn([
        '/usr/bin/env', 'PYTHONPATH=' + lemonade,
        lemonade + '/bin/lemonade',
        '-s',                   # Write statistics to stdout.
        path_y,
    ])
    commit(path_y, path_py, path_sha256)

class local_build_py(build_py):
    def run(self):
        for grammar in grammars:
            generate_parser(lemonade, grammar)
        build_py.run(self)

install_requires = [
    'numpy>=1.8',
    'scipy>=0.13',
    # Plotf, MRipl
    'matplotlib>=1.1',
    # Saving and restoring ripls
    'dill',
    # Plotf
    'patsy', # Because ggplot needs this installed first ??
    'pandas>=0.14, <0.16', # <0.16 because that version introduces a change that breaks ggplot
    'ggplot',
    # Debug pictures of scaffolds
    'networkx',
    # Ripl server
    'flask>=0.10',
    'requests>=1.2',
    # IPython magics; MRipl
    'ipython>=1.2',
    'ipyparallel',
    'pyzmq>=13',
    'jsonschema', # Ubuntu 14.04 apparently needs this mentioned for notebooks to work
]

tests_require = [
    'nose>=1.3',
    'nose-testconfig>=0.9',
    'nose-ignore-docstring>=0.2',
    'nose-cov>=1.6',
    'flaky',
    'pexpect',
    'seaborn', # For examples/gaussian_geweke.py
    'statsmodels', # For examples/gaussian_geweke.py
    'cython', # Because it has to be installed before pystan, and pip
              # does the wrong thing with ordering packages pulled in
              # as dependencies.
    'pystan', # For testing the venstan integration
    'markdown2', # For building the tutorial with venture-transcript
    # TODO Is markdown2 a real dependency?
]

# XXX For inexplicable reasons, during sdist.run, setuptools quietly
# modifies self.distribution.metadata.version to replace plus signs by
# hyphens -- even where they are explicitly allowed by PEP 440.
# distutils does not do this -- only setuptools.
class local_sdist(sdist):
    # This is not really a subcommand -- it's actually a predicate to
    # determine whether to run a subcommand.  So modifying anything in
    # it is a little evil.  But it'll do.
    def fixidioticegginfomess(self):
        self.distribution.metadata.version = version
        return False
    sub_commands = [('sdist_fixidioticegginfomess', fixidioticegginfomess)]

setup (
    name = 'venture',
    version = version,
    author = 'MIT Probabilistic Computing Project',
    author_email = 'venture-dev@lists.csail.mit.edu',
    url = 'http://probcomp.csail.mit.edu/venture/',
    long_description = 'TBA.',
    install_requires = install_requires,
    tests_require = tests_require,
    extras_require = {
        'tests': tests_require,
    },
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
    scripts = ['script/venture', 'script/vendoc'],
    cmdclass={
        'build_py': local_build_py,
        'sdist': local_sdist,
    },
)
