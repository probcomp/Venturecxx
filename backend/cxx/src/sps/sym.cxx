#include "sps/sym.h"
#include "value.h"
#include "node.h"

VentureValue * IsSymbolSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  return new VentureBool(dynamic_cast<VentureSymbol*>(node->operandNodes[0]->getValue()));
}



