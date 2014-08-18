Venture
=======

Venture is an interactive, Turing-complete probabilistic programming
platform that aims to be sufficiently expressive, extensible, and
efficient for general-purpose use.

http://probcomp.csail.mit.edu/venture/

Venture is rapidly-evolving, **alpha quality** research software. The
key ideas behind its design and implementation have yet to be
published. We are making Venture available at this early stage
primarily to facilitate collaboration and support the emerging
probabilistic programming community.

Installing Venture from Source
==============================

This release is for early adopter types who are
willing to put up with much of the pain that a more mature software
package would not impose.  In particular, documentation is sparse and
the user interface is unforgiving.  Often, the only way to learn
what's going on will be to ask us or to read the source code.

Dependencies (Ubuntu)
---------------------

Here is what we install on a clean Ubuntu (works best in 14.04 or higher).

    # Get system dependencies
    sudo apt-get install -y libboost-all-dev libgsl0-dev python-pip ccache libfreetype6-dev
    # Must update distribute before requirements.txt install
    sudo pip install -U distribute

    # [Optional] Get Python dependencies (faster to install prepackaged than via pip)
    # Also pulls in required external libraries
    # HOWEVER, version skew problems have been reported if installing
    # python-numpy and python-scipy via apt-get on older versions of Ubuntu
    sudo apt-get install -y python-pyparsing python-flask python-requests python-numpy python-matplotlib python-scipy python-zmq ipython

    # [Optional] Get dependencies for ggplot (needed for the built-in plotting facilities)
    # Note: on older versions of Ubuntu, install them via pip (see "Install ggplot" below)
    sudo apt-get install -y python-pandas python-patsy

Dependencies (OSX, Homebrew)
----------------------------

This is the best-supported and best-tested method for building Venture on Mac.
    
    # Install Packet Manager "Homebrew"
    http://brew.sh/

    # Install the current Homebrew version of gcc / g++ (4.9 at time of writing)
    # see this thread: http://apple.stackexchange.com/questions/38222/how-do-i-install-gcc-via-homebrew
    brew install gcc

    # Install libraries using homebrew
    brew install python ccache gsl

The one slightly tricky step is installing Boost. The difficulty comes from the fact that GNU c++ compilers use the standard library libstdc++, while Mac's c++ compiler on Mavericks uses libc++. In order for Venture to build, you must build Boost using libstdc++, and then build Venture using the same. This can be accomplished by building both Boost and Venture using Homebrew (GNU) gcc / g++ instead of Mac's compiler. The correct version of gcc is set for Venture installation in the setup.py file. The install Boost with the correct library, call:

    brew install boost --with-python --cc=gcc-4.9

Finally, install Python dependencies:

    # [Optional] Get Python dependencies (faster to install prepackaged than via pip)
    # Also pulls in required external libraries
    pip install ipython
    pip install pyparsing flask numpy matplotlib scipy

Dependencies (OSX, macports)
----------------------------

This installation method is not as well-tested as Homebrew. It may break.

For macports installation instructions see: [https://www.macports.org/install.php](https://www.macports.org/install.php)

```
# System dependencies
sudo port install \
    gcc_select gcc49 ccache \
    python_select python27 \
    pip_select py27-pip \
    virtualenv_select virtualenv \
    boost gsl
```

```
# [Optional] Python dependencies
sudo port install \
    py27-flask \
    py27-ipython \
    py27-matplotlib \
    py27-numpy \
    py27-parsing \
    py27-requests \
    py27-scipy \
    py27-zmq \
```

Macports allows side-by-side installation of multiple versions of gcc, python, ipython, etc. In order to set the default versions of each of these, do

    sudo port select gcc mp-gcc49
    sudo port select python python27
    sudo port select ipython ipython27
    sudo port select pip pip27
    sudo port select virtualenv virtualenv27


System-Wide Installation
------------------------

Install any remaining dependencies by doing

    sudo pip install -r requirements.txt

[Optional] Install ggplot (needed for the built-in plotting facilities)

    sudo pip install ggplot

On Linux systems and OSX with Homebrew, now simply do

    sudo python setup.py install

On OSX with Macports, run

    ./global_install_osx_macports.sh


Local Installation
------------------

In order to install locally, download and install python "virtualenv" onto your computer. [https://pypi.python.org/pypi/virtualenv](https://pypi.python.org/pypi/virtualenv)

Create a new virtual environment to install the requirements:

    virtualenv env.d

If Python dependencies were pre-installed these can be used by typing

    virtualenv --system-site-packages env.d

Activate the environment, and install any remaining dependencies

    source env.d/bin/activate
    pip install -r requirements.txt

[Optional] Install ggplot (needed for the built-in plotting facilities)

    sudo pip install ggplot

On Linux and OSX with Homebrew, now install by typing

    python setup.py install

If using macports, run

    ./install_osx_macports.sh



Checking that your installation was successful
----------------------------------------------

    ./sanity_tests.sh

If you are interested in improving Venture, you can also run

    ./list_known_issues.sh

Getting Started
---------------

-   Interactive Venture console:

        venture

    You might like to type in the [trick coin
    example](http://probcomp.csail.mit.edu/venture/console-examples.html)
    to start getting a feel for Venture.

-   Venture as a library in Python:

        python -i -c 'from venture import shortcuts; ripl = shortcuts.Puma().make_church_prime_ripl()'

    Using Venture as a library allows you to drive it
    programmatically.  You might like to peruse the
    [examples](http://probcomp.csail.mit.edu/venture/library-examples.html)
    for inspiration.

-   You can find two advanced examples in the `examples/`
    directory---`examples/lda.py` and `examples/crosscat.py` These
    rely on VentureUnit (included), an experimental inference
    visualization wrapper using Venture as a library.


Developing Venture
==================

The interesting parts of the code are:
- The frontend stack (including SIVM, RIPL, VentureUnit, server, and Python client) in `python/`.
- The pure-Python, clearer, normative Lite backend in `backend/lite/`.
- The C++, faster Puma backend (plus a thin Python driver) in `backend/puma/`.
- The test suite lives under `test/`.
- The actual entry points are in `script/`, notably `script/venture`.
- Advanced example programs live in `examples/`.
- There are some developer tools available in `tool/`.
- There is a stale C++11 backend in `backend/cxx/`.
- The Javascript client and web demos are actually in the
  [VentureJSRIPL](https://github.com/mit-probabilistic-computing-project/VentureJSRIPL)
  repository.
- There are language-level benchmarks (and correctness tests) in the
  [VentureBenchmarksAndTests](https://github.com/mit-probabilistic-computing-project/VentureBenchmarksAndTests)
  repository, but they may have bit rotted by now.

Python Development
------------------

We recommend using ipython for Venture development; you can obtain it
via

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
