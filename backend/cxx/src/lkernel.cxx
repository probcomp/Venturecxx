#include "lkernel.h"

VentureValuePtr   DefaultAAALKernel::simulate(Trace * trace,VentureValuePtr oldValue,Args * args) { throw 500; }
double DefaultAAALKernel::weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,Args * args) { throw 500; }

VentureValuePtr DeterministicLKernel::simulate(Trace * trace,VentureValuePtr oldValue,Args * args) { throw 500; }
double DeterministicLKernel::weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,Args * args) { throw 500; }
