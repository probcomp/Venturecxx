#ifndef DIR_MULT_H
#define DIR_MULT_H

#include "types.h"
#include "psp.h"
#include "args.h"
#include "sp.h"

struct DirMultSPAux : SPAux
{
  DirMultSPAux(int n);
  vector<int> counts;
};

struct DirMultSP : VentureSP
{
  DirMultSP(PSP * requestPSP, PSP * outputPSP, int n);
  shared_ptr<SPAux> constructSPAux() const;
  int n;
};

// TODO not implemented
struct DirMultOutputPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value,shared_ptr<Args> args) const;
};

struct MakeSymDirMultOutputPSP : PSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  bool childrenCanAAA() const { return true; }
};

struct SymDirMultOutputPSP : RandomPSP
{
  SymDirMultOutputPSP(double alpha, size_t n) : alpha(alpha), n(n) {}

  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value,shared_ptr<Args> args) const;
  void incorporate(VentureValuePtr value,shared_ptr<Args> args) const;
  void unincorporate(VentureValuePtr value,shared_ptr<Args> args) const;

private:
  double alpha;
  size_t n;
};

#endif
