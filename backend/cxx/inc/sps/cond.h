#ifndef BRANCH_SP_H
#define BRANCH_SP_H



#include "sp.h"

#include <vector>
#include <string>

struct BranchSP : SP
{
  BranchSP(): SP("branch")
    {
      makesESRs = true;
      isESRReference = true;
      canAbsorbRequest = false;
    }
  VentureValue * simulateRequest(Node * node, gsl_rng * rng) const override;
  void flushRequest(VentureValue * value) const override;

};

struct ExpBranchSP : SP
{
  ExpBranchSP(): SP("branch")
    {
      makesESRs = true;
      isESRReference = true;
      canAbsorbRequest = false;
    }
  VentureValue * simulateRequest(Node * node, gsl_rng * rng) const override;
};

struct BiplexSP : SP
{
  BiplexSP(): SP("biplex") {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  void flushOutput(VentureValue * value) const override;

};




#endif
