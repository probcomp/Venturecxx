#ifndef MSP_H
#define MSP_H

#include "psp.h"
#include "args.h"

struct MakeMSPOutputPSP : PSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct MSPRequestPSP : PSP
{
  MSPRequestPSP(Node * sharedOperatorNode);

  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  bool canAbsorb(ConcreteTrace * trace,Node * appNode,Node * parentNode) const { return true; }

private:
  Node * sharedOperatorNode;
};

#endif
