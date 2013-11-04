#ifndef MAKE_SYM_DIR_MULT_H
#define MAKE_SYM_DIR_MULT_H


#include "sp.h"
#include "spaux.h"
#include <vector>
#include <string>

/* TODO this does not yet handle n changing in AAA */
struct SymDirMultSPAux : SPAux
{
  /* TODO confirm vector initializes doubles to 0 */
  SymDirMultSPAux(uint32_t n): counts(n,0) {}
  // counts could be uints, but then we need to keep converting to add alpha
  vector<uint32_t> counts;
};

struct MakeSymDirMultSP : SP
{
  MakeSymDirMultSP()
    {
      childrenCanAAA = true;
    }
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;

};

struct SymDirMultSP : SP
{
  SymDirMultSP(double alpha,uint32_t n): alpha(alpha), n(n)
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

  double alpha;
  uint32_t n;
};



#endif
