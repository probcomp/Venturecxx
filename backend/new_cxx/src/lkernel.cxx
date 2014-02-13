#include "lkernel.h"

VentureValuePtr   DefaultAAALKernel::simulate(Trace * trace,VentureValuePtr oldValue,shared_ptr<Args> args,gsl_rng * rng) { assert(false); }
double DefaultAAALKernel::weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,shared_ptr<Args> args) { assert(false); }

VentureValuePtr DeterministicLKernel::simulate(Trace * trace,VentureValuePtr oldValue,shared_ptr<Args> args,gsl_rng * rng) { assert(false); }
double DeterministicLKernel::weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,shared_ptr<Args> args) { assert(false); }
