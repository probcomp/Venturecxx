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
  MSPRequestPSP* copy_help(ForwardingMap* m) const;

private:
  Node * sharedOperatorNode;
};

#endif
