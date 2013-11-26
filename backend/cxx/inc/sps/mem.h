#ifndef MEM_H
#define MEM_H

#include "all.h"
#include "sp.h"
#include "spaux.h"
#include <vector>
#include <string>
#include <unordered_map>

struct MSPAux : SPAux
{
// VentureValue *: a vector of the arguments
// size_t: id
// uint32_t: count
  unordered_map<VentureValue*,pair<size_t,uint32_t> > ids;
  size_t nextID = 0;
  ~MSPAux();
};

struct MakeMSP : SP
{
  MakeMSP(): SP("make_msp") {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};

struct MSP : SP
{
  MSP(string address, Node * sharedOperatorNode): 
    SP("msp @ " + address),
    sharedOperatorNode(sharedOperatorNode)
    {
      makesESRs = true;
      isESRReference = true;
      canAbsorbRequest = false;
      name = "msp";
    }

  VentureValue * simulateRequest(Node * node, gsl_rng * rng) const override;
  void flushRequest(VentureValue * value) const override;

  Node * sharedOperatorNode;

  VentureValue* makeVectorOfArgs(const vector<Node *> & operandNodes) const;
  
  void incorporateRequest(VentureValue * value, Node * node) const override;
  void removeRequest(VentureValue * value, Node * node) const override;

  SPAux * constructSPAux() const override;
  void destroySPAux(SPAux * spaux) const override;

};



#endif
