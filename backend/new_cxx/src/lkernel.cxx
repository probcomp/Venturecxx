#include "lkernel.h"

VentureValuePtr   DefaultAAALKernel::simulate(Trace * trace,VentureValuePtr oldValue,shared_ptr<Args> args) { throw 500; }
double DefaultAAALKernel::weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,shared_ptr<Args> args) { throw 500; }

VentureValuePtr DeterministicLKernel::simulate(Trace * trace,VentureValuePtr oldValue,shared_ptr<Args> args) { throw 500; }
double DeterministicLKernel::weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,shared_ptr<Args> args) { throw 500; }
