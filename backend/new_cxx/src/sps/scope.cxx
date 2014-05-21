#include "sps/scope.h"
#include "node.h"
#include <boost/assign/list_of.hpp>

VentureValuePtr ScopeIncludeOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return args->operandValues[2];
}
 
bool ScopeIncludeOutputPSP::canAbsorb(ConcreteTrace * trace,ApplicationNode * appNode,Node * parentNode) const
{
  return parentNode != appNode->operandNodes[2];
}

vector<VentureValuePtr> ScopeIncludeOutputPSP::gradientOfSimulate(const shared_ptr<Args> args, const VentureValuePtr value, const VentureValuePtr direction) const {
  return boost::assign::list_of(VentureNumber::makeValue(0))(VentureNumber::makeValue(0))(direction);
}
VentureValuePtr ScopeExcludeOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return args->operandValues[1];
}
 
bool ScopeExcludeOutputPSP::canAbsorb(ConcreteTrace * trace,ApplicationNode * appNode,Node * parentNode) const
{
  return parentNode != appNode->operandNodes[1];
}
