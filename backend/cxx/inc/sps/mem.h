#ifndef MEM_H
#define MEM_H

#include "sp.h"
#include "spaux.h"
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
      name = "msp";
    }

  VentureValue * simulateRequest(Node * node, gsl_rng * rng) const override;
  void flushRequest(VentureValue * value) const override;

  size_t hashValues(vector<Node *> operands) const;
  size_t preprocessHashValue(size_t h) const;
  Node * sharedOperatorNode;
};



#endif
