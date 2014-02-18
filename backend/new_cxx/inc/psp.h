#ifndef PSP_H
#define PSP_H

#include "types.h"
#include <vector>
#include "args.h"

#include <gsl/gsl_rng.h>

struct LKernel;
struct ConcreteTrace;
struct ApplicationNode;

using std::vector;

struct PSP
{
  virtual VentureValuePtr simulate(shared_ptr<Args> args,gsl_rng * rng) const =0;
  virtual double logDensity(VentureValuePtr value,shared_ptr<Args> args) const { return 0; }
  virtual void incorporate(VentureValuePtr value,shared_ptr<Args> args) const {}
  virtual void unincorporate(VentureValuePtr value,shared_ptr<Args> args) const {}

  virtual bool isRandom() const { return false; }
  virtual bool canAbsorb(ConcreteTrace * trace,ApplicationNode * appNode,Node * parentNode) const { return false; }

  virtual bool childrenCanAAA() const { return false; }
  virtual shared_ptr<LKernel> const getAAALKernel();

  virtual bool canEnumerateValues(shared_ptr<Args> args) const { return false; }
  virtual vector<VentureValuePtr> enumerateValues(shared_ptr<Args> args) const { return vector<VentureValuePtr>(); }

  virtual double logDensityOfCounts(shared_ptr<SPAux> spAux) const { assert(false); }
  // TODO variational is punted for now
  // virtual bool hasVariationalLKernel() const { return false; }
  // virtual shared_ptr<LKernel> getVariationalLKernel(ConcreteTrace * trace,Node * node) const;

  // TODO special psp-specific lkernels are punted for now
  // virtual bool hasSimulationKernel() const { return false; }
  // virtual bool hasDeltaKernel() const { return false; }
};

struct NullRequestPSP : PSP
{
  VentureValuePtr simulate(shared_ptr<Args> args,gsl_rng * rng) const;
  bool canAbsorb(ConcreteTrace * trace,ApplicationNode * appNode,Node * parentNode) const { return true; }
};

struct ESRRefOutputPSP : PSP
{
  VentureValuePtr simulate(shared_ptr<Args> args,gsl_rng * rng) const;
  bool canAbsorb(ConcreteTrace * trace,ApplicationNode * appNode,Node * parentNode) const;
};

struct RandomPSP : PSP
{
  bool isRandom() const { return true; }
  bool canAbsorb(ConcreteTrace * trace,ApplicationNode * appNode,Node * parentNode) const { return true; }
};

#endif
