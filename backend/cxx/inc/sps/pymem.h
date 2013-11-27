#ifndef PYMEM_H
#define PYMEM_H

#include "sp.h"
#include "spaux.h"
#include "sps/pycrp.h"

// Note these SPs are for rendering only. Very minimal attention to correctness and 
// features such as AAA.
struct MakePYMemSP : SP
{ 
  MakePYMemSP() 
    {
//      childrenCanAAA = true;
    }

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 

};

struct PYMemSP : SP
{ 
  PYMemSP(Node * sharedOperatorNode,double alpha, double d): 
    sharedOperatorNode(sharedOperatorNode),
    alpha(alpha), 
    d(d)
    { 
      makesESRs = true;
      isESRReference = true;
      name = "pymem";
      tracksSamples = true;
      isRandomRequest = true;
      canAbsorbRequest = true;
    }

  SPAux * constructSPAux() const override { return new PitmanYorCRPSPAux; }
  void destroySPAux(SPAux *spaux) const { delete spaux; }

  VentureValue * simulateRequest(Node * node, gsl_rng * rng) const override; 
  double logDensityRequest(VentureValue * value, Node * node) const override; 

  void incorporateRequest(VentureValue * value, Node * node) const override; 
  void removeRequest(VentureValue * value, Node * node) const override; 

  Node * sharedOperatorNode;
  double alpha;
  double d;
};


#endif
