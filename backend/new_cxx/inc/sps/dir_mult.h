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

// TODO not implemented
struct DirMultOutputPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value,shared_ptr<Args> args) const;
};

// Collapsed
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

  double logDensityOfCounts(shared_ptr<SPAux> spAux) const;

private:
  double alpha;
  size_t n;
};

// Uncollapsed 
struct UCSymDirMultSP : SP
{
  UCSymDirMultSP(PSP * requestPSP, PSP * outputPSP): SP(requestPSP,outputPSP) {}

  bool hasAEKernel() const { return true; }
  void AEInfer(shared_ptr<Args> args,gsl_rng * rng) const;
};

struct UCDirMultSPAux : DirMultSPAux
{
  UCDirMultSPAux(int n, double * theta): DirMultSPAux(n), theta(theta) {}
  double * theta; // TODO GC delete[] this in the destructor
};

struct MakeUCSymDirMultOutputPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;
};

struct UCSymDirMultOutputPSP : RandomPSP
{
  UCSymDirMultOutputPSP(size_t n) : n(n) {}

  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value,shared_ptr<Args> args) const;
  void incorporate(VentureValuePtr value,shared_ptr<Args> args) const;
  void unincorporate(VentureValuePtr value,shared_ptr<Args> args) const;

private:
  size_t n;
};

#endif
