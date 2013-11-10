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

struct MSPAux : SPAux
{
  map<size_t, vector<VentureValue*> > ownedValues;
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
  void flushFamily(SPAux * spaux, size_t id) const override;
  SPAux * constructSPAux() const override { return new MSPAux; }
  void destroySPAux(SPAux * spaux) const override;

  size_t hashValues(vector<Node *> operands) const;
  Node * sharedOperatorNode;
};



#endif
