import sys, os

from distutils.core import setup, Extension
import distutils.ccompiler

setup (name = 'venture',
       version = '1.0',
       description = 'Testing',
       author = 'MIT Probabilistic Computing Project',
       author_email = 'venture-dev@lists.csail.mit.edu',
       url = 'TBA',
       long_description = '''
TBA.
''',
       py_modules = ["venture.client", "venture.sugars_processor", "venture.lisp_parser", "venture.utils"])
