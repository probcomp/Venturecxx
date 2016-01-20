The last time someone installed Venture Puma directly on a Mac and
told us how they did it was in September of 2014 and looked like this
the following.  It's probably easier to get Venture running on Ubuntu
in a virtual machine (for example, a [Docker](https://www.docker.com/)
container).  Or you can use Venture without Puma; you'll get better
error messages that way anyway.

Dependencies (Homebrew)
----------------------------

    # Install Packet Manager "Homebrew"
    http://brew.sh/

    # Install the current Homebrew version of gcc / g++ (4.9 at time of writing)
    # see this thread: http://apple.stackexchange.com/questions/38222/how-do-i-install-gcc-via-homebrew
    brew install gcc

    # Install libraries using homebrew
    brew install python ccache gsl

The one slightly tricky step is installing Boost and Boost.Python. The
difficulty comes from the fact that GNU c++ compilers use the standard
library libstdc++, while Mac's c++ compiler on Mavericks uses
libc++. In order for Venture Puma to build, you must build Boost using
libstdc++, and then build Venture using the same. This can be
accomplished by building both Boost and Venture using GNU gcc
(installed via Homebrew) instead of Mac's compiler. The correct
version of gcc is set for Venture installation in the setup.py
file. To install Boost with the correct library, call:

    brew install boost --cc=gcc-4.9
    brew install boost-python --cc=gcc-4.9

Dependencies (macports)
----------------------------

For instructions to install macports see:
[https://www.macports.org/install.php](https://www.macports.org/install.php)

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

Installation
------------

    pip install venture-0.4.2.tar.gz
