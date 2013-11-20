#include "value.h"
#include "lkernel.h"
#include "node.h"
#include "sp.h"

#include <iostream>

VentureValue * DefaultAAAKernel::simulate(const VentureValue * oldVal, const Args & args, LatentDB * latentDB,gsl_rng * rng) 
{
  return makerSP->simulateOutput(args,rng);
}

double DefaultAAAKernel::weight(const VentureValue * newVal, const VentureValue * oldVal, const Args & args, LatentDB * latentDB)
{
  VentureSP * vsp = dynamic_cast<VentureSP *>(newVal);
  assert(vsp);

  double weight = vsp->sp->logDensityOfCounts(args.madeSPAux);
  LPRINT("DefaultAAAKernel::weight(): ", weight);
  return weight;
}

VentureValue * DeterministicLKernel::simulate(const VentureValue * oldVal, const Args & args, LatentDB * latentDB,gsl_rng * rng)
{
  return value;
}

double DeterministicLKernel::weight(const VentureValue * newVal, const VentureValue * oldVal, const Args & args, LatentDB * latentDB)
{
  assert(newVal == value);
  return sp->logDensity(value,args);
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

vector<double> DefaultVariationalLKernel::gradientOfLogDensity(const VentureValue * output,
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
    if (parameterScopes[i] == ParameterScope::POSITIVE_REAL && 
        parameters[i] < 0.1)
    {
      parameters[i] = 0.1;
    }
  }
}

VentureValue * DefaultVariationalLKernel::simulate(const VentureValue * oldVal, const Args & args, LatentDB * latentDB,gsl_rng * rng)
{
  double output = sp->simulateOutputNumeric(parameters,rng);
  assert(isfinite(output));
  return new VentureNumber(output);
}

double DefaultVariationalLKernel::weight(const VentureValue * newVal, const VentureValue * oldVal, const Args & args, LatentDB * latentDB) 
{
  VentureNumber * varg1 = dynamic_cast<VentureNumber*>(args.operands[0]);
  VentureNumber * varg2 = dynamic_cast<VentureNumber*>(args.operands[1]);
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
