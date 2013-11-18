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
  MSPAux * clone() const override; // TODO implement
  unordered_map<VentureValue*,pair<size_t,uint32_t> > ids;
  size_t nextID = 0;
  ~MSPAux();
};

struct MSPMakerSP : SP
{
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
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

  VentureValue * simulateRequest(const Args & args, gsl_rng * rng) const override;
  void flushRequest(VentureValue * value) const override;

  Node * sharedOperatorNode;
  
  void incorporateRequest(VentureValue * value, const Args & args) const override;
  void removeRequest(VentureValue * value, const Args & args) const override;

  SPAux * constructSPAux() const override;
  void destroySPAux(SPAux * spaux) const override;

};



#endif
