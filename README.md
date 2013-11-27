Venture
=======

Venture is an interactive, Turing-complete probabilistic programming
platform that aims to be sufficiently expressive, extensible, and
efficient for general-purpose use.

http://probcomp.csail.mit.edu/venture/

Venture is **alpha quality** software.  We are proud of the underlying
engine and the ideas it embodies, but we have not sanded off its many
rough edges.

Installing Venture from Source
==============================

Be advised that this release is for early adopter types who are
willing to put up with much of the pain that a more mature software
package would not impose.  In particular, documentation is sparse and
the user interface is unforgiving.  Often, the only way to learn
what's going on will be to ask us or to read the source code.

Dependencies
------------

On Ubuntu:

    sudo apt-get install python-dev libboost-python-dev libgsl0-dev
    
GCC 4.8 is also required for c++11 support.

One approach to installing GCC 4.8 on Ubuntu is to do all of the following:

    # get non C++11 system dependencies (boost1.48-all may be redundant)
    sudo apt-get install -y libboost1.48-all-dev libgsl0-dev cmake make git

    # get C++11 and install it as the default gcc and g++
    sudo apt-get install -y python-software-properties
    sudo add-apt-repository -y ppa:ubuntu-toolchain-r/test
    sudo apt-get update
    sudo apt-get install -y gcc-4.8 g++-4.8
    sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-4.8 50
    sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-4.8 50

Installation to global environment
----------------------------------

    sudo pip install -r requirements.txt
    sudo python setup.py install

Installation to local environment
---------------------------------

Download and install python "virtualenv" onto your computer.
https://pypi.python.org/pypi/virtualenv

Create a new virtual environment to install the requirements:

    virtualenv env.d
    source env.d/bin/activate
    pip install -r requirements.txt

Installation into your virtual environment:

    python setup.py install

Checking that your installation was successful
----------------------------------------------

    ./sanity_tests.sh

If you are interested in improving Venture, you can also run

    ./list_known_issues.sh

Getting Started
---------------

-   Interactive Venture console:

        venture

    You might like to type in the trick coin example to start getting
    a feel for Venture.

-   Venture as a library in Python:

        python -i -c 'from venture import shortcuts; ripl = shortcuts.make_church_prime_ripl()'

    Using Venture as a library allows you to drive it
    programmatically.  You might like to peruse the brief tutorial for
    inspiration.

-   You can find two advanced examples in the `examples/` directory.
    These rely on VentureUnit (included), an experimental inference
    visualization wrapper using Venture as a library.


Developing Venture
==================

The interesting parts of the code are:
- The stack (including SIVM, RIPL, VentureUnit, server, and Python client) in `python/`
- The C++11 engine (plus a thin Python driver) in `backend/cxx/`
- The actual entry points are in `script/`
- The Javascript client and web demos are actually in the
  [VentureJSRIPL](https://github.com/mit-probabilistic-computing-project/VentureJSRIPL)
  repository.
- There are language-level benchmarks (and correctness tests) in the
  [VentureBenchmarksAndTests](https://github.com/mit-probabilistic-computing-project/VentureBenchmarksAndTests)
  repository.

Python Development
------------------

We recommend using ipython for Venture development; you can obtain it via

    pip install ipython

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
