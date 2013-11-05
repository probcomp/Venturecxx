#include "value.h"
#include "lkernel.h"
#include "node.h"
#include "sp.h"

VentureValue * DefaultAAAKernel::simulate(VentureValue * oldVal, Node * appNode, LatentDB * latentDB,gsl_rng * rng) 
{
  return makerSP->simulateOutput(appNode,rng);
}

double DefaultAAAKernel::weight(VentureValue * newVal, VentureValue * oldVal, Node * appNode, LatentDB * latentDB)
{
  VentureSP * vsp = dynamic_cast<VentureSP *>(newVal);
  assert(vsp);

  double weight = vsp->sp->logDensityOfCounts(appNode->madeSPAux);
  LPRINT("DefaultAAAKernel::weight(): ", weight);
  return weight;
}

VentureValue * DeterministicLKernel::simulate(VentureValue * oldVal, Node * appNode, LatentDB * latentDB,gsl_rng * rng)
{
  return value;
}

double DeterministicLKernel::weight(VentureValue * newVal, VentureValue * oldVal, Node * appNode, LatentDB * latentDB)
{
  assert(newVal == value);
  return sp->logDensity(value,appNode);
}


DefaultVariationalLKernel::DefaultVariationalLKernel(SP * sp,Node * node):
  sp(sp)
{
  for (Node * operandNode : node->operandNodes)
  {
    VentureNumber * vnum = dynamic_cast<VentureNumber*>(operandNode->getValue());
    assert(vnum);
    parameters.push_back(vnum->x);
  }
  parameterScopes = sp->getParameterScopes();
}

vector<double> DefaultVariationalLKernel::gradientOfLogDensity(VentureValue * output,
							       const vector<double> & arguments) const
{
  VentureNumber * vnum = dynamic_cast<VentureNumber*>(output);
  assert(vnum);
  return sp->gradientOfLogDensity(vnum->x, arguments);
}


void DefaultVariationalLKernel::updateParameters(const vector<double> & gradient, double gain, double stepSize)
{
  for (int i = 0; i < parameters.size(); ++i)
  {
    parameters[i] += gradient[i] *  gain * stepSize;
    if (parameterScopes[i] == ParameterScope::POSITIVE_REAL && 
        parameters[i] < 0.01)
    {
      parameters[i] = 0.01;
    }
  }
}
