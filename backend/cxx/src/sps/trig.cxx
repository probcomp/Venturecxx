#include "node.h"
#include "sp.h"
#include "sps/trig.h"
#include "value.h"
#include <cmath>
#include <cassert>
#include <vector>

VentureValue * SinSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  VentureNumber * vnum = dynamic_cast<VentureNumber*>(node->operandNodes[0]->getValue());
  assert(vnum);
  return new VentureNumber(sin(vnum->x));
}

VentureValue * CosSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  VentureNumber * vnum = dynamic_cast<VentureNumber*>(node->operandNodes[0]->getValue());
  assert(vnum);
  return new VentureNumber(cos(vnum->x));
}
