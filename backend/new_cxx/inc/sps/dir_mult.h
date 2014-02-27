#ifndef DIR_MULT_H
#define DIR_MULT_H

#include "types.h"
#include "psp.h"
#include "args.h"
#include "sp.h"

// Collapsed SPAux
struct DirMultSPAux : SPAux
{
  DirMultSPAux(int n) : counts(n, 0) {}
  vector<int> counts;
  shared_ptr<SPAux> clone();
};

// Collapsed Symmetric

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

// Collapsed Asymmetric
struct MakeDirMultOutputPSP : PSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  bool childrenCanAAA() const { return true; }
};

struct DirMultOutputPSP : RandomPSP
{
  DirMultOutputPSP(const vector<double>& alpha) : alpha(alpha) {}

  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value,shared_ptr<Args> args) const;
  void incorporate(VentureValuePtr value,shared_ptr<Args> args) const;
  void unincorporate(VentureValuePtr value,shared_ptr<Args> args) const;

  double logDensityOfCounts(shared_ptr<SPAux> spAux) const;

private:
  vector<double> alpha;
};

// Uncollapsed SPAux
struct UCDirMultSPAux : DirMultSPAux
{
  UCDirMultSPAux(int n): DirMultSPAux(n), theta(n,0) {}
  shared_ptr<SPAux> clone();
  vector<double> theta;
};

// Uncollapsed Symmetric
struct MakeUCSymDirMultOutputPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;
};

struct UCSymDirMultSP : SP
{
  UCSymDirMultSP(PSP * requestPSP, PSP * outputPSP): SP(requestPSP,outputPSP) {}

  bool hasAEKernel() const { return true; }
  void AEInfer(shared_ptr<SPAux> spAux, shared_ptr<Args> args,gsl_rng * rng) const;
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

// Uncollapsed Asymmetric
struct MakeUCDirMultOutputPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;
};

struct UCDirMultSP : SP
{
  UCDirMultSP(PSP * requestPSP, PSP * outputPSP): SP(requestPSP,outputPSP) {}

  bool hasAEKernel() const { return true; }
  void AEInfer(shared_ptr<SPAux> spAux, shared_ptr<Args> args,gsl_rng * rng) const;
};

struct UCDirMultOutputPSP : RandomPSP
{
  UCDirMultOutputPSP(size_t n) : n(n) {}

  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value,shared_ptr<Args> args) const;
  void incorporate(VentureValuePtr value,shared_ptr<Args> args) const;
  void unincorporate(VentureValuePtr value,shared_ptr<Args> args) const;

private:
  size_t n;
};


#endif
