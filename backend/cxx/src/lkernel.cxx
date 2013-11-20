#include "value.h"
#include "lkernel.h"
#include "node.h"
#include "sp.h"
#include <cfloat>
#include <cmath>
#include <iostream>

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


DefaultVariationalLKernel::DefaultVariationalLKernel(const SP * sp,Node * node):
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
							       Node * node) const
{

  VentureNumber * voutput = dynamic_cast<VentureNumber*>(output);
  assert(voutput);

  vector<double> arguments;

  for (Node * operandNode : node->operandNodes)
  {
    VentureNumber * vparam = dynamic_cast<VentureNumber*>(operandNode->getValue());
    assert(vparam);
    arguments.push_back(vparam->x);
  }


  return sp->gradientOfLogDensity(voutput->x, arguments);
}


void DefaultVariationalLKernel::updateParameters(const vector<double> & gradient, double gain, double stepSize)
{
  for (size_t i = 0; i < parameters.size(); ++i)
  {
    parameters[i] += gradient[i] *  gain * stepSize;
    if (parameters[i] > DBL_MAX) { parameters[i] = DBL_MAX; }
    if (parameters[i] < -DBL_MAX) { parameters[i] = -DBL_MAX; }
    if (parameterScopes[i] == ParameterScope::POSITIVE_REAL && 
        parameters[i] < 0.1)
    {
      parameters[i] = 0.1;
    }
    assert(isfinite(parameters[i]));
  }
}

VentureValue * DefaultVariationalLKernel::simulate(VentureValue * oldVal, Node * appNode, LatentDB * latentDB,gsl_rng * rng)
{
  double output = sp->simulateOutputNumeric(parameters,rng);
  assert(isfinite(output));
  return new VentureNumber(output);
}

double DefaultVariationalLKernel::weight(VentureValue * newVal, VentureValue * oldVal, Node * appNode, LatentDB * latentDB) 
{
  VentureNumber * varg1 = dynamic_cast<VentureNumber*>(appNode->operandNodes[0]->getValue());
  VentureNumber * varg2 = dynamic_cast<VentureNumber*>(appNode->operandNodes[1]->getValue());
  VentureNumber * voutput = dynamic_cast<VentureNumber*>(newVal);
  assert(varg1);
  assert(varg2);
  assert(voutput);

  double ld = sp->logDensityOutputNumeric(voutput->x,{varg1->x,varg2->x});
  assert(isfinite(ld));
  double proposalLd = sp->logDensityOutputNumeric(voutput->x,parameters);
  assert(isfinite(proposalLd));
  return ld - proposalLd;
}
