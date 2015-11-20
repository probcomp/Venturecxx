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

Installation
============

This release is for early adopter types who are
willing to put up with much of the pain that a more mature software
package would not impose.  In particular, documentation is sparse and
the user interface is unforgiving.  Often, the only way to learn
what's going on will be to ask us or to read the source code.

Ubuntu
------

    sudo apt-get install -y libboost-all-dev libgsl0-dev ccache
    sudo apt-get install -y python-matplotlib  # If you don't already have it
    sudo apt-get install -y python-scipy       # If you don't already have it
    pip install venture-0.4.2.tar.gz

OSX
---

We do not officially support installing Venture directly on OSX.
Installation with pip should work, but we are not routinely testing
it:

    SKIP_PUMA_BACKEND=1 pip install venture-0.4.2.tar.gz

If this doesn't work or you want Puma, you could

- Run Venture in a [Docker](https://www.docker.com/) container (see
  our testing [Docker
  file](https://github.com/probcomp/Venturecxx/blob/master/script/jenkins/debian-test-docker/Dockerfile)
  for inspiration), or

- Have a look at [how someone managed to get Venture running on a mac
  in September 2014](https://github.com/probcomp/Venturecxx/blob/master/doc/stale-mac-install-instructions.md)

The Puma backend is an optional faster VentureScript engine written in
C++.

Checking that your installation was successful
----------------------------------------------

For a quick check that should catch most installation problems, unpack
the source distribution and run

    ./tool/check_capabilities.sh

in it, or

    SKIP_PUMA_BACKEND=1 ./tool/check_capabilities.sh

if you didn't install the Puma backend.

For a more thorough check, you can run our development test suite.

This requires installing the test dependencies:

    pip intall --find-links /path/to/tarball/directory venture[tests]

and then

    ./sanity_tests.sh

or

    ./sanity_tests.sh lite

if you didn't install the Puma backend.

Getting Started
---------------

-   Interactive Venture console:

        venture

-   Run a VentureScript program:

        venture -f <file>.vnts

-   You might like to go through the [Venture
    tutorial](http://probcomp.csail.mit.edu/venture/latest/tutorial/)

-   Venture as a library in Python:

        python -i -c 'from venture import shortcuts; ripl = shortcuts.Puma().make_church_prime_ripl()'

    Using Venture as a library allows you to drive it
    programmatically.

-   You can find several examples in the `examples/` directory.

-   There is a [reference manual](http://probcomp.csail.mit.edu/venture/latest/reference/)

Developing Venture
==================

You can build a local version of the refence manual from the `refman/`
directory.  This requires Sphinx; see instructions in the README there.

The interesting parts of the code are:
- There is a live tutorial in `examples/tutorial/part*` (run an
  ipython notebook server in that directory)
- The frontend stack (including SIVM, RIPL, server, and Python client) in `python/`.
- The pure-Python, clearer, normative Lite backend in `backend/lite/`.
- The C++, faster Puma backend (plus a thin Python driver) in `backend/puma/`.
- The test suite lives under `test/`.
- The actual entry points are in `script/`, notably `script/venture`.
- Advanced example programs live in `examples/`.
- There are some developer tools available in `tool/`.
- The Javascript client and web demos are in `demos/`, subdivided by
  architecture into `demos/jsripl` (which corresponds to the erstwile
  VentureJSRIPL repository), `demos/elm` (an attempt to do demos in
  Elm), and `demos/hill-curve-fitting`, which is a single demo that
  exemplifies web sockets.
- There are language-level benchmarks (and correctness tests) in the
  [VentureBenchmarksAndTests](https://github.com/probcomp/VentureBenchmarksAndTests)
  repository, but they may have bit rotted by now.
