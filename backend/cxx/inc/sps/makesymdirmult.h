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
  SPAux * clone() const override;

  // counts could be uints, but then we need to keep converting to add alpha
  vector<uint32_t> counts;
};

struct MakeSymDirMultSP : SP
{
  MakeSymDirMultSP()
    {
      childrenCanAAA = true;
      name = "make_sym_dir_mult";
    }
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;

};

struct SymDirMultSP : SP
{
  SymDirMultSP(double alpha,uint32_t n): alpha(alpha), n(n)
    {
      isRandomOutput = true;
      canAbsorbOutput = true;
      tracksSamples = true;
      name = "sym_dir_mult";
    }

  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, const Args & args) const override;
  void incorporateOutput(VentureValue * value, const Args & args) const override;
  void removeOutput(VentureValue * value, const Args & args) const override;

  double logDensityOfCounts(SPAux * spaux) const;

  SPAux * constructSPAux() const override;
  void destroySPAux(SPAux * spaux) const override;

  double alpha;
  uint32_t n;
};



#endif
