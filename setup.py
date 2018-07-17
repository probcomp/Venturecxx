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
    from setuptools.command.test import test as test_py
except ImportError:
    from distutils.core import setup, Extension
    from distutils.cmd import Command
    from distutils.command.build_py import build_py
    from distutils.command.sdist import sdist

    class test_py(Command):
        def __init__(self, *args, **kwargs):
            Command.__init__(self, *args, **kwargs)
        def initialize_options(self): pass
        def finalize_options(self): pass
        def run(self): self.run_tests()
        def run_tests(self): Command.run_tests(self)
        def set_undefined_options(self, opt, val):
            Command.set_undefined_options(self, opt, val)

import os
import subprocess
import sys

def get_version():
    import re
    import subprocess
    # git describe a commit using the most recent tag reachable from it.
    # Release tags start with v* (XXX what about other tags starting with v?)
    # and are of the form `v1.1.2`.
    #
    # The output `desc` will be of the form v1.1.2-2-gb92bef6[-dirty]:
    # - verpart     v1.1.2
    # - revpart     2
    # - localpart   gb92bef6[-dirty]
    desc = subprocess.check_output([
        'git', 'describe', '--dirty', '--long', '--match', 'v*',
    ])
    match = re.match(r'^v([^-]*)-([0-9]+)-(.*)$', desc)
    assert match is not None
    verpart, revpart, localpart = match.groups()
    # Create a post version.
    if revpart > '0' or 'dirty' in localpart:
        # Local part may be g0123abcd or g0123abcd-dirty.
        # Hyphens not kosher here, so replace by dots.
        localpart = localpart.replace('-', '.')
        full_version = '%s.post%s+%s' % (verpart, revpart, localpart)
    # Create a release version.
    else:
        full_version = verpart

    # Strip the local part if there is one, to appease pkg_resources,
    # which handles only PEP 386, not PEP 440.
    if '+' in full_version:
        pkg_version = full_version[:full_version.find('+')]
    else:
        pkg_version = full_version

    # Sanity-check the result.  XXX Consider checking the full PEP 386
    # and PEP 440 regular expressions here?
    assert '-' not in full_version, '%r' % (full_version,)
    assert '-' not in pkg_version, '%r' % (pkg_version,)
    assert '+' not in pkg_version, '%r' % (pkg_version,)

    return pkg_version, full_version

pkg_version, full_version = get_version()

def write_version_py(path):
    try:
        with open(path, 'rb') as f:
            version_old = f.read()
    except IOError:
        version_old = None
    version_new = '__version__ = %r\n' % (full_version,)
    if version_old != version_new:
        print 'writing %s' % (path,)
        with open(path, 'wb') as f:
            f.write(version_new)

ON_LINUX = 'linux' in sys.platform
ON_MAC = 'darwin' in sys.platform

cflags = os.getenv("CFLAGS", "").split()

if ON_LINUX:
    os.environ['CC'] = 'ccache gcc '
if ON_MAC:
    os.environ['CC'] = 'ccache gcc'
    os.environ['CXX'] = 'ccache g++'
    os.environ['CFLAGS'] = "-std=c++11 -stdlib=libc++ -mmacosx-version-min=10.7"

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
    "venture.ggplot",
    "venture.ggplot.components",
    "venture.ggplot.coords",
    "venture.ggplot.exampledata",
    "venture.ggplot.geoms",
    "venture.ggplot.scales",
    "venture.ggplot.stats",
    "venture.ggplot.tests",
    "venture.ggplot.themes",
    "venture.ggplot.utils",
    "venture.lite",
    "venture.lite.infer",
    "venture.untraced",
    "venture.parser",
    "venture.parser.church_prime",
    "venture.parser.venture_script",
    "venture.plex",
    "venture.plots",
    "venture.plugins",
    "venture.puma",
    "venture.ripl",
    "venture.server",
    "venture.shortcuts",
    "venture.sivm",
    "venture.test",
    "venture.test.properties",
    "venture.value",
]

if ON_LINUX:
    puma = Extension("venture.puma.libpumatrace",
        libraries = ['gsl', 'gslcblas', 'boost_python', 'boost_system', 'boost_thread'],
        extra_compile_args = ["-Wall", "-g", "-O2", "-fPIC", "-fno-omit-frame-pointer"] + cflags,
        #undef_macros = ['NDEBUG', '_FORTIFY_SOURCE'],
        include_dirs = puma_inc_dirs,
        sources = puma_src_files)
if ON_MAC:
    puma = Extension("venture.puma.libpumatrace",
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
        sha256_in = sha256_file(path_in).hexdigest()
        sha256_out = sha256_file(path_out).hexdigest()
        expected = bytes('%s\n%s\n' % (sha256_in, sha256_out))
        with open(path_sha256, 'rb') as file_sha256:
            actual = file_sha256.read(len(expected))
            if actual != expected or file_sha256.read(1) != '':
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
        write_version_py(version_py)
        for grammar in grammars:
            generate_parser(lemonade, grammar)
        build_py.run(self)

def parse_req_file(filename):
    def parse_req_line(line):
        return line.split('#')[0].strip()
    return [parse_req_line(line)
            for line in open(filename).read().splitlines()
            if len(parse_req_line(line)) > 0]

class local_test(test_py):
    def acknowledge_missing_egg(self, req):
        '''To mirror self.distribution.fetch_build_egg, but report instead.'''
        # req is a Requirements object:
        # https://pythonhosted.org/setuptools/pkg_resources.html
        pass  #

    def check_build_eggs(self, requires, **kwargs):
        '''To mirror self.distribution.fetch_build_eggs, but don't fetch.'''
        import pkg_resources
        pkg_resources.working_set.resolve(
            pkg_resources.parse_requirements(requires),
            installer=self.acknowledge_missing_egg,
        )  # Resolve will raise DistributionNotFound for missing deps.

    def run(self):
        if '-n' in sys.argv or '--dry-run' in sys.argv:
            # I can't believe self._dry_run exists but does not get set.
            if self.distribution.install_requires:
                self.check_build_eggs(self.distribution.install_requires)
            if self.distribution.tests_require:
                self.check_build_eggs(self.distribution.tests_require)
            self.run_tests()
        else:
            test_py.run(self)

    def run_tests(self):
        status = subprocess.check_output('git submodule status --recursive',
                                         shell=True)
        for line in status.split('\n'):
            if not line: continue
            if line[0] == '-':
                print status
                raise ImportError("Missing submodules."
                                  " Consider running"
                                  " `git submodule update --init --recursive`.")
        print "Test prerequisites satisfied."
        print "Please use ./check.sh instead and read ./HACKING.md"
        sys.exit(0)  # A success(!) because we have what tests_require.

tests_require = [
    'nose>=1.3',
    'nose-testconfig>=0.9',
    'nose-cov>=1.6',
    'pexpect',
    'markdown2', # For building the tutorial with venture-transcript
     # TODO Is markdown2 a real dependency?
]

# Make sure the VERSION file in the sdist is exactly specified, even
# if it is a development version, so that we do not need to run git to
# discover it -- which won't work because there's no .git directory in
# the sdist.
class local_sdist(sdist):
    def make_release_tree(self, base_dir, files):
        import os
        sdist.make_release_tree(self, base_dir, files)
        version_file = os.path.join(base_dir, 'VERSION')
        print('updating %s' % (version_file,))
        # Write to temporary file first and rename over permanent not
        # just to avoid atomicity issues (not likely an issue since if
        # interrupted the whole sdist directory is only partially
        # written) but because the upstream sdist may have made a hard
        # link, so overwriting in place will edit the source tree.
        with open(version_file + '.tmp', 'wb') as f:
            f.write('%s\n' % (pkg_version,))
        os.rename(version_file + '.tmp', version_file)

# XXX These should be attributes of `setup', but helpful distutils
# doesn't pass them through when it doesn't know about them a priori.
version_py = 'python/lib/version.py'

setup (
    name = 'venture',
    version = pkg_version,
    author = 'MIT Probabilistic Computing Project',
    author_email = 'venture-dev@lists.csail.mit.edu',
    url = 'http://probcomp.csail.mit.edu/venture/',
    long_description = 'TBA.',
    tests_require = tests_require,
    extras_require = {
        'tests': tests_require,
    },
    packages = packages,
    package_dir = {
        "venture": "python/lib",
        "venture.ggplot": "external/ggplot/dist/ggplot",
        "venture.lite": "backend/lite",
        "venture.untraced": "backend/untraced",
        "venture.plex": "external/plex/dist/Plex",
        "venture.puma": "backend/new_cxx",
        "venture.test": "test",
    },
    package_data = {
        '': ['*.vnt'],
        'venture.ggplot': [
            'tests/baseline_images/%s/*' % (x,)
            for x in os.listdir(
                    'external/ggplot/dist/ggplot/tests/baseline_images')
        ] + [
            'exampledata/*.csv',
            'geoms/*.png',
        ],
    },
    ext_modules = ext_modules,
    scripts = ['script/venture', 'script/vendoc'],
    cmdclass={
        'build_py': local_build_py,
        'sdist': local_sdist,
        'test': local_test,
    },
)
