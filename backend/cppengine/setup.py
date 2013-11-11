# From here:
# http://docs.python.org/2/extending/building.html#building

# Just build as a Python library: python setup.py build
# Build and install to the system: sudo python setup.py build install

import sys, os

from distutils.core import setup, Extension
import distutils.ccompiler

def user_input(question):
  print "*** " + question
  user_input = raw_input("Please, specify: (y)es or (n)o?")
  if user_input == "y":
    return True
  elif user_input == "n":
    return False
  else:
    return user_input(question)
    
def check_for_library(library_name):
  # Found here: http://www.cac.cornell.edu/wiki/index.php?title=Python_Distutils_Tips#How_to_find_if_a_library_exists
  test_compiler = distutils.ccompiler.new_compiler(force=1)
  test_compiler.add_library(library_name)
  return test_compiler.has_function('rand', libraries=[]) # "rand" is just an arbitrary function, nothing special.
  
boost_system_library_name = ""
if check_for_library("boost_system-mt"):
  boost_system_library_name = "boost_system-mt"
elif check_for_library("boost_system"):
  boost_system_library_name = "boost_system"
else:
  print "*** Error. Neither boost_system-mt nor boost_system have been found."
  print "*** Please, install boost, boost-development, boost_system, boost_thread."
  print "*** Details: http://www.yuraperov.com/MIT.PCP/wiki/index.php5?title=Installation"
  sys.exit("")
  
boost_thread_library_name = ""
if check_for_library("boost_system-mt"):
  boost_thread_library_name = "boost_system-mt"
elif check_for_library("boost_system"):
  boost_thread_library_name = "boost_system"
else:
  print "*** Error. Neither boost_thread-mt nor boost_thread have been found."
  print "*** Please, install boost, boost-development, boost_system, boost_thread."
  print "*** Details: http://www.yuraperov.com/MIT.PCP/wiki/index.php5?title=Installation"
  sys.exit("")
  
venture_libraries = ['gsl', 'gslcblas', 'pthread', boost_system_library_name, boost_thread_library_name] # 'profiler'
venture_extra_compile_args = [] # ['-O2']

import platform
if platform.mac_ver()[0] != '':
  print "*** Notice: It seems you are using Mac. Adding the flag '-mmacosx-version-min=10.7'"
  venture_extra_compile_args += ['-mmacosx-version-min=10.7']
  
# venture_libraries += ['profiler']
# venture_extra_compile_args += ['-D_VENTURE_USE_GOOGLE_PROFILER']

module1 = Extension('_engine',
                    define_macros = [('MAJOR_VERSION', '1'),
                                     ('MINOR_VERSION', '0')],
                    # include_dirs = ['/usr/include/python' + str(sys.version_info[0]) + '.' + str(sys.version_info[1])],
                    libraries = venture_libraries,
                    extra_compile_args = venture_extra_compile_args,
                    #library_dirs = ['/usr/local/lib'],
                    sources = ['Utilities.cpp', 'VentureValues.cpp', 'VentureParser.cpp', 'Primitives.cpp', 'Evaluator.cpp', 'Main.cpp', 'XRPCore.cpp', 'XRPmem.cpp', 'XRPs.cpp', 'RIPL.cpp', 'Analyzer.cpp', 'ERPs.cpp', 'MHProposal.cpp', 'PythonProxy.cpp', 'Shell_PPPs.cpp'])
#-lpython2.6 -lgsl -lgslcblas

setup (name = 'venture',
       version = '1.0',
       description = 'Testing',
       author = 'MIT Probabilistic Computing Project',
       author_email = 'venture-dev@lists.csail.mit.edu',
       url = 'TBA',
       long_description = '''
TBA.
''',
       ext_package = "venture",
       ext_modules = [module1],
       py_modules = ["venture.client", "venture.sugars_processor", "venture.rest_server", "venture.lisp_parser", "venture.engine", "venture.utils"])
