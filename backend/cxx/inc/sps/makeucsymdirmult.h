#ifndef MAKE_UC_SYM_DIR_MULT_H
#define MAKE_UC_SYM_DIR_MULT_H



#include "exp.h"
#include "sp.h"
#include "spaux.h"
#include <vector>
#include <string>


#include "lkernel.h"

struct MakeUCSymDirMultAAAKernel : LKernel
{
  VentureValue * simulate(VentureValue * oldVal, Node * appNode, LatentDB * latentDB, gsl_rng * rng) override;
  double weight(VentureValue * newVal, VentureValue * oldVal, Node * appNode, LatentDB * latentDB) override;

};

struct MakeUCSymDirMultSP : SP
{
  MakeUCSymDirMultSP()
    {
      childrenCanAAA = true;
      isRandomOutput = true;
      canAbsorbOutput = true;
    }
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, Node * node) const override;
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

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, Node * node) const override;
  void incorporateOutput(VentureValue * value, Node * node) const override;
  void removeOutput(VentureValue * value, Node * node) const override;

  double logDensityOfCounts(SPAux * spaux) const;

  SPAux * constructSPAux() const override;
  void destroySPAux(SPAux * spaux) const override;

  ~UCSymDirMultSP() { delete[] theta; }

  double * theta;
  uint32_t n;
};


#endif
