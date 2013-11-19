
#include "sp.h"
#include "sps/trig.h"
#include "value.h"
#include <cmath>
#include <cassert>
#include <vector>

VentureValue * SinSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
  VentureNumber * vnum = dynamic_cast<VentureNumber*>(args.operands[0]);
  assert(vnum);
  return new VentureNumber(sin(vnum->x));
}

VentureValue * CosSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
  VentureNumber * vnum = dynamic_cast<VentureNumber*>(args.operands[0]);
  assert(vnum);
  return new VentureNumber(cos(vnum->x));
}
