#include "value.h"
#include "lkernel.h"
#include "node.h"
#include "sp.h"
#include <cmath>
#include <cfloat>
#include <iostream>

VentureValue * DefaultAAAKernel::simulate(VentureValue * oldVal, const Args & args, LatentDB * latentDB,gsl_rng * rng) 
{
  return makerSP->simulateOutput(args,rng);
}

double DefaultAAAKernel::weight(VentureValue * newVal, VentureValue * oldVal, const Args & args, LatentDB * latentDB)
{
  VentureSP * vsp = dynamic_cast<VentureSP *>(newVal);
  assert(vsp);

  double weight = vsp->sp->logDensityOfCounts(args.madeSPAux);
  LPRINT("DefaultAAAKernel::weight(): ", weight);
  return weight;
}

VentureValue * DeterministicLKernel::simulate(VentureValue * oldVal, const Args & args, LatentDB * latentDB,gsl_rng * rng)
{
  return value;
}

double DeterministicLKernel::weight(VentureValue * newVal, VentureValue * oldVal, const Args & args, LatentDB * latentDB)
{
  assert(newVal == value);
  return sp->logDensity(value,args);
}


DefaultVariationalLKernel::DefaultVariationalLKernel(const SP * sp,const Args & args):
  sp(sp)
{
  for (VentureValue * operand : args.operands)
  {
    VentureNumber * vnum = dynamic_cast<VentureNumber*>(operand);
    assert(vnum);
    parameters.push_back(vnum->x);
  }
  parameterScopes = sp->getParameterScopes();
}

vector<double> DefaultVariationalLKernel::gradientOfLogDensity(VentureValue * output,
							       const Args & args) const
{

  VentureNumber * voutput = dynamic_cast<VentureNumber*>(output);
  assert(voutput);

  vector<double> arguments;

  for (VentureValue * operand : args.operands)
  {
    VentureNumber * vparam = dynamic_cast<VentureNumber*>(operand);
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
    if (parameters[i] < -DBL_MAX) { parameters[i] = -DBL_MAX; }
    if (parameters[i] > DBL_MAX) { parameters[i] = DBL_MAX; }

  }
}

VentureValue * DefaultVariationalLKernel::simulate(VentureValue * oldVal, const Args & args, LatentDB * latentDB,gsl_rng * rng)
{
  double output = sp->simulateOutputNumeric(parameters,rng);
  assert(isfinite(output));
  return new VentureNumber(output);
}

double DefaultVariationalLKernel::weight(VentureValue * newVal, VentureValue * oldVal, const Args & args, LatentDB * latentDB) 
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
