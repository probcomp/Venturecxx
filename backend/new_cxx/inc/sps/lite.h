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

struct ForeignLitePSP : PSP
{
  ForeignLitePSP(boost::python::object psp): psp(psp) {}

  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;

  void incorporate(VentureValuePtr value,shared_ptr<Args> args) const;
  void unincorporate(VentureValuePtr value,shared_ptr<Args> args) const;

  bool isRandom() const;
  bool canAbsorb(ConcreteTrace * trace,ApplicationNode * appNode,Node * parentNode) const;

  bool canEnumerateValues(shared_ptr<Args> args) const;
  vector<VentureValuePtr> enumerateValues(shared_ptr<Args> args) const;

  boost::python::object psp;
};

struct ForeignLiteSPAux : SPAux
{
  ForeignLiteSPAux(boost::python::object sp): aux(sp.attr("constructSPAux")()) {}
  boost::python::object aux;
};

struct ForeignLiteSP : SP
{
  // TODO: requestPSP (needs requests to be stackable)
  ForeignLiteSP(boost::python::object sp): SP(new NullRequestPSP(),
                                              new ForeignLitePSP(sp.attr("outputPSP"))),
                                           sp(sp) {}
  boost::python::dict toPython(Trace * trace, shared_ptr<SPAux> spAux) const;

  boost::python::object sp;
};

#endif
