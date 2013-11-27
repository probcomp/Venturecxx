#ifndef BNP_H
#define BNP_H

#include "sp.h"
#include "spaux.h"
/* Bayesian non-parametric distributions. */


struct PitmanYorCRPSPAux : SPAux
{
  uint32_t nextIndex{0};
  uint32_t numCustomers{0};
  uint32_t numTables{0};
  map<uint32_t,uint32_t> tableCounts;
};

struct MakePitmanYorCRPSP : SP
{ 
  MakePitmanYorCRPSP() 
    {
      childrenCanAAA = true;
    }

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 

};


/* Two parameter generalization of the CRP */
struct PitmanYorCRPSP : SP
{ 
  PitmanYorCRPSP(double alpha, double d): 
    alpha(alpha), 
    d(d)
    { 
      tracksSamples = true;
      isRandomOutput = true;
      canAbsorbOutput = true;
      name = "pycrp";
    }

  SPAux * constructSPAux() const override { return new PitmanYorCRPSPAux; }
  void destroySPAux(SPAux *spaux) const { delete spaux; }

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
  double logDensityOutput(VentureValue * value, Node * node) const override; 

  void incorporateOutput(VentureValue * value, Node * node) const override; 
  void removeOutput(VentureValue * value, Node * node) const override; 

  double logDensityOfCounts(SPAux * spaux) const;

  double alpha;
  double d;
};








#endif
