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

If you want to compile and install the C++ extentions (necessary
if you want to run a local server), then run:

    python setup.py install --with-local-engine

The compiler may complain about missing C++ libraries, in which case
you should install them separately before compiling. TODO: compile
a list of C++ dependencies for various operating systems


Installation to global environment
==================================

Exactly the same as above, except you don't need to install "virtualenv".

    # Make sure you are not in an active virtualenv
    deactivate

    sudo pip install -r requirements.txt
    sudo python setup.py install [--with-local-engine]


No installation at all
======================

To speed up the development process, you can run the python
files directly from the source tree without installing the
venture module. All you need to do is set the global PYTHONPATH
to the directory containing this README.md file. For example,
to run one of the tests, you need to type:

    PYTHONPATH=$PWD python ./tests/name_of_test_file.py

Though, you will not be able to import the C++ Venture
extention using this method.
