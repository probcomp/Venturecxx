#ifndef MAKE_UC_SYM_DIR_MULT_H
#define MAKE_UC_SYM_DIR_MULT_H



#include "sp.h"
#include "spaux.h"
#include <vector>
#include <string>


#include "lkernel.h"

struct MakeUCSymDirMultAAAKernel : LKernel
{
  VentureValue * simulate(const VentureValue * oldVal, const Args & args, LatentDB * latentDB, gsl_rng * rng) override;
  double weight(const VentureValue * newVal, const VentureValue * oldVal, const Args & args, LatentDB * latentDB) override;

};

struct MakeUCSymDirMultSP : SP
{
  MakeUCSymDirMultSP()
    {
      childrenCanAAA = true;
      isRandomOutput = true;
      canAbsorbOutput = true;
    }
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, const Args & args) const override;
  LKernel * getAAAKernel() const override { return new MakeUCSymDirMultAAAKernel; }

};

struct UCSymDirMultSP : SP
{
  UCSymDirMultSP(double * theta, uint32_t n): theta(theta), n(n)
    {
      isRandomOutput = true;
      canAbsorbOutput = true;
      tracksSamples = true;
    }

  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, const Args & args) const override;
  void incorporateOutput(VentureValue * value, const Args & args) const override;
  void removeOutput(VentureValue * value, const Args & args) const override;

  double logDensityOfCounts(SPAux * spaux) const;

  SPAux * constructSPAux() const override;
  void destroySPAux(SPAux * spaux) const override;

  ~UCSymDirMultSP() { delete[] theta; }

  double * theta;
  uint32_t n;
};


#endif
