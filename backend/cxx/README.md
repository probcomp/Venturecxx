VentureCXX Integration Part I
================================

Note on installation:

One needs to install g++ >4.8, gsl, cmake, and boost, and maybe others. 

To build, enter:

> cmake .

> make

Note on status:

We are passing a very basic test in tests.py. Good start! I am sure there are sloppy mistakes in regen and detach--I will read through them more carefully, but first I think it is easier to find simple errors through asserts firing on some basic programs.

Also, we only have a tiny number of SPs. I need to implement flip, categorical, VentureAtom, dirichlet, MEM, and such before being able to run many important tests.