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

private:
  double alpha;
  size_t n;
};

// Uncollapsed 
struct UCSymDirMultSP : SP
{
  bool hasAEKernel() const { return true; }
  void AEInfer(shared_ptr<SPAux> madeSPAux) const;
};

struct UCDirMultSPAux : DirMultSPAux
{
  UCDirMultSPAux(int n, double * theta): DirMultSPAux(n), theta(theta) {}
  double * theta;
  vector<int> counts;
};

struct MakeUCSymDirMultOutputPSP : PSP
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
