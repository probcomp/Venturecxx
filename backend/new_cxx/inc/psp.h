#ifndef PSP_H
#define PSP_H

#include "types.h"
#include <vector>

using std::vector;

struct PSP
{
  virtual VentureValuePtr simulate(Args * args) const =0;
  virtual double logDensity(VentureValuePtr value,Args * args) const { return 0; }
  virtual void incorporate(VentureValuePtr value,Args * args) const {}
  virtual void unincorporate(VentureValuePtr value,Args * args) const {}

  virtual bool isRandom() const { return false; }
  virtual bool canAbsorb(ConcreteTrace * trace,Node * appNode,Node * parentNode) const { return false; }

  virtual bool childrenCanAAA() const { return false; }
  virtual shared_ptr<LKernel> const getAAALKernel(self);

  virtual bool canEnumerateValues(Args * args) const { return false; }
  virtual vector<VentureValuePtr> enumerateValues(Args * args) const { return vector<VentureValuePtr>(); }

  // TODO variational is punted for now
  // virtual bool hasVariationalLKernel() const { return false; }
  // virtual shared_ptr<LKernel> getVariationalLKernel(ConcreteTrace * trace,Node * node) const;

  // TODO special psp-specific lkernels are punted for now
  // virtual bool hasSimulationKernel() const { return false; }
  // virtual bool hasDeltaKernel() const { return false; }
};

struct NullRequestPSP : PSP
{
  VentureValuePtr simulate(Args * args) const override;
  bool canAbsorb(ConcreteTrace * trace,Node * appNode,Node * parentNode) const override { return true; }
};

struct ESRRefOutputPSP : PSP
{
  VentureValuePtr simulate(Args * args) const override;
  bool canAbsorb(ConcreteTrace * trace,Node * appNode,Node * parentNode) const override;
};

struct RandomPSP(PSP)
{
  bool isRandom() const override { return true; }
  bool canAbsorb(ConcreteTrace * trace,Node * appNode,Node * parentNode) const override { return true; }
};

#endif
