#ifndef MAKE_DIR_MULT_H
#define MAKE_DIR_MULT_H

#include "sp.h"
#include "spaux.h"
#include <vector>
#include <string>

/* TODO this does not yet handle n changing in AAA */
struct DirMultSPAux : SPAux
{
  DirMultSPAux(uint32_t n): counts(n,0) {}
  vector<uint32_t> counts;
};

struct MakeDirMultSP : SP
{
  MakeDirMultSP()
    {
      childrenCanAAA = true;
      name = "make_dir_mult";
    }
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;

};

struct DirMultSP : SP
{
  DirMultSP(vector<double> alphaVector): alphaVector(alphaVector)
    {
      isRandomOutput = true;
      canAbsorbOutput = true;
      tracksSamples = true;
      name = "dir_mult";
    }

  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, const Args & args) const override;
  void incorporateOutput(VentureValue * value, const Args & args) const override;
  void removeOutput(VentureValue * value, const Args & args) const override;

  double logDensityOfCounts(SPAux * spaux) const;

  SPAux * constructSPAux() const override;
  void destroySPAux(SPAux * spaux) const override;

  vector<double> alphaVector;

};



#endif
