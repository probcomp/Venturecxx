#include "sps/sym.h"
#include "value.h"


VentureValue * IsSymbolSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  return new VentureBool(dynamic_cast<VentureSymbol*>(args.operands[0]));
}



