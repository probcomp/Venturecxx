#include "sps/scope.h"
#include "node.h"

VentureValuePtr ScopeIncludeOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return args->operandValues[2];
}
 
bool ScopeIncludeOutputPSP::canAbsorb(ConcreteTrace * trace,ApplicationNode * appNode,Node * parentNode) const
{
  return parentNode != appNode->operandNodes[2];
}

VentureValuePtr ScopeExcludeOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return args->operandValues[1];
}
 
bool ScopeExcludeOutputPSP::canAbsorb(ConcreteTrace * trace,ApplicationNode * appNode,Node * parentNode) const
{
  return parentNode != appNode->operandNodes[1];
}
