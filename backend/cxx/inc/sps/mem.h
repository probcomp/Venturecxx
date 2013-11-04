#ifndef MEM_H
#define MEM_H

#include "sp.h"
#include <vector>
#include <string>

struct MSPMakerSP : SP
{
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};

struct MSP : SP
{
  MSP(Node * sharedOperatorNode): 
    sharedOperatorNode(sharedOperatorNode)
    {
      makesESRs = true;
      isESRReference = true;
      canAbsorbRequest = false;
    }

  VentureValue * simulateRequest(Node * node, gsl_rng * rng) const override;
  void flushRequest(VentureValue * value) const override;
  size_t hashValues(vector<Node *> operands) const;
  Node * sharedOperatorNode;
};



#endif
