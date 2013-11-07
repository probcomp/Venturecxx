Venture
=======

The primary implementation of the Venture system lives here.

Interesting parts:
- The stack (including RIPL, SIVM, server, and Python client) in `python/`
- The C++11 engine (plus a thin Python driver) in `backend/cxx/`
- The Javascript client and web demos are actually in the
  [VentureJSRIPL](https://github.com/mit-probabilistic-computing-project/VentureJSRIPL)
  repository.
- There are language-level benchmarks (and correctness tests) in the
  [VentureBenchmarksAndTests](https://github.com/mit-probabilistic-computing-project/VentureBenchmarksAndTests)
  repository.
- There is an inference visualization tool in the [VentureUnit](https://github.com/mit-probabilistic-computing-project/VentureUnit) repository.

Requirements
============

On Ubuntu:

    sudo apt-get install python-dev libboost-python-dev libgsl0-dev
    
GCC 4.8 is also required for c++11 support.

Installation to local environment
=================================

Download and install python "virtualenv" onto your computer.
https://pypi.python.org/pypi/virtualenv

Create a new virtual environment to install the requirements:

    virtualenv env.d
    source env.d/bin/activate
    pip install -r requirements.txt

Installation into your virtual environment:

    python setup.py install

We recommend using ipython for Venture development; you can obtain it via

    pip install ipython

Checking that your installation was successful
===============================================

./sanity_tests.sh

If you are interested in improving Venture, you can also run

./list_known_issues.sh

Notes for Ubuntu
==================================

- Start with an Ubuntu 12.04 VM
- Follow steps in:
  https://github.com/mit-probabilistic-computing-project/vm-install-venture/blob/master/provision_venture.sh

Rapid Python Development
==================================

If you are developing the python libraries, you will
likely be running the installation script hundreds of
times. This is very slow if you don't have a c++ compiler
cache installed. Here is a quick shell command (aliased in
my bashrc file) which automatically resets the virtual
environment and reinstalls the module, using the compiler
cache. Make sure that the additional python dependencies
are installed in the global python environment.

    deactivate && rm -rf env.d build && virtualenv --system-site-packages env.d && \
      . env.d/bin/activate && CC="ccache gcc" python setup.py install
