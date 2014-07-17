#ifndef SPS_LITE_H
#define SPS_LITE_H

#include <boost/python.hpp>
#include <boost/python/object.hpp>

#include "types.h"
#include "sp.h"
#include "psp.h"

// A mechanism for calling foreign SPs (written in Python, using the
// Lite interface) in Puma. Implemented as a Puma SP which wraps a
// ForeignLiteSP object (defined in lite/foreign.py), which in turn
// wraps a Lite SP. The Puma half handles value translation from C++
// to stack dicts, while the Lite half handles value translation from
// stack dicts to Lite VentureValues.

struct ForeignLiteOutputPSP : PSP
{
  ForeignLiteOutputPSP(boost::python::object sp): sp(sp) {}

  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;

  boost::python::object sp;
};

struct ForeignLiteSP : SP
{
  // TODO: requests, and add a ForeignLiteRequestPSP or something
  ForeignLiteSP(boost::python::object sp): SP(new NullRequestPSP(),
                                              new ForeignLiteOutputPSP(sp)) {}
};

#endif
