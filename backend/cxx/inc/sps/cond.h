#ifndef BRANCH_SP_H
#define BRANCH_SP_H



#include "sp.h"

#include <vector>
#include <string>

struct BranchSP : SP
{
  BranchSP()
    {
      makesESRs = true;
      isESRReference = true;
      canAbsorbRequest = false;
    }
  VentureValue * simulateRequest(const Args & args, gsl_rng * rng) const override;
  void flushRequest(VentureValue * value) const override;

};

struct BiplexSP : SP
{

  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
  void flushOutput(VentureValue * value) const override;

};




#endif
