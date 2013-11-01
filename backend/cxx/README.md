VentureCXX Integration Part I
================================

One needs to install gsl, cmake, and boost, and maybe others. 

To build, enter:

> cmake .

> make

> ipython trace.py

This should print a message indicating that the C++ received the
call from Python. 

The next step is to flesh out Trace::evalExpression in wrapper.cxx
so that we parse the boost::python::object into an Expression object.

Notes:

1. The Expression class is not stable yet.
2. Be careful parsing the different kinds of VentureValues.

I will be able to get this working on Monday, and the rest of the integration
should be straightforward.
