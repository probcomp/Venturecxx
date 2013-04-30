
# From here:
# http://docs.python.org/2/extending/building.html#building

# Just build as a Python library: python setup.py build
# Build and install to the system: sudo python setup.py build install

from distutils.core import setup, Extension
import sys
import os

# venture_libraries += ['profiler']
# venture_extra_compile_args += ['-D_VENTURE_USE_GOOGLE_PROFILER']
#-lpython2.6 -lgsl -lgslcblas

venture_libraries = ['gsl', 'gslcblas', 'pthread', 'boost_system', 'boost_thread', 'profiler']
venture_extra_compile_args = ['-O2']

venture_sources =[
    'Utilities.cpp',
    'VentureValues.cpp',
    'VentureParser.cpp',
    'Primitives.cpp',
    'Evaluator.cpp',
    'Main.cpp',
    'XRPCore.cpp',
    'XRPmem.cpp',
    'XRPs.cpp',
    'RIPL.cpp',
    'Analyzer.cpp',
    'ERPs.cpp',
    'MHProposal.cpp',
    'PythonProxy.cpp'
    ]
venture_sources = [os.path.abspath(os.path.join(os.path.dirname(__file__),'..','src',x)) for x in venture_sources]


ext_modules = []
packages=["venture","venture.vim","venture.ripl",
    "venture.parser","venture.server","venture.shortcuts",
    "venture.test"]

if '--without-cpp-engine' in sys.argv:
    sys.argv.remove('--without-cpp-engine')
else:
    cpp_engine = Extension('venture.vim._cpp_engine_extension',
                        define_macros = [('MAJOR_VERSION', '1'),
                                         ('MINOR_VERSION', '0')],
                        libraries = venture_libraries,
                        extra_compile_args = venture_extra_compile_args,
                        sources = venture_sources)
    ext_modules.append(cpp_engine)

setup (name = 'Venture engine',
       version = '1.0',
       description = 'Testing',
       author = 'MIT.PCP',
       author_email = 'yura.perov@gmail.com',
       url = 'TBA',
       long_description = 'TBA.',
       packages = packages,
       package_dir={"venture":"lib", "venture.test":"test"},
       ext_modules = ext_modules
       )
