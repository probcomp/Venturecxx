#include "node.h"
#include "sp.h"
#include "sps/bool.h"
#include "value.h"
#include <cassert>
#include <vector>

VentureValue * BoolAndSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
  VentureBool * b1 = dynamic_cast<VentureBool *>(args.operands[0]);
  VentureBool * b2 = dynamic_cast<VentureBool *>(args.operands[1]);
  assert(b1);
  assert(b2);
  return new VentureBool(b1->pred && b2->pred);
}

VentureValue * BoolOrSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
  VentureBool * b1 = dynamic_cast<VentureBool *>(args.operands[0]);
  VentureBool * b2 = dynamic_cast<VentureBool *>(args.operands[1]);
  assert(b1);
  assert(b2);
  return new VentureBool(b1->pred || b2->pred);
}

VentureValue * BoolNotSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
    VentureBool * b = dynamic_cast<VentureBool *>(args.operands[0]);
    assert(b);
    return new VentureBool(!b->pred);
}

VentureValue * BoolXorSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
  VentureBool * b1 = dynamic_cast<VentureBool *>(args.operands[0]);
  VentureBool * b2 = dynamic_cast<VentureBool *>(args.operands[1]);
  assert(b1);
  assert(b2);
  return new VentureBool((b1->pred && !b2->pred) || (b2->pred && !b1->pred));
}

