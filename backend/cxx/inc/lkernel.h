#ifndef LKERNEL_H
#define LKERNEL_H

#include "omegadb.h"
#include "gsl/gsl_rng.h"

struct SP;

enum class ParameterScope { REAL, POSITIVE_REAL };

struct LKernel
{
  virtual VentureValue * simulate(VentureValue * oldVal, const Args & args,gsl_rng * rng) =0;
  virtual double weight(VentureValue * newVal, VentureValue * oldVal, const Args & args) { return 0; };
  virtual double reverseWeight(VentureValue * oldVal, const Args & args)
    { return weight(oldVal,nullptr,args); }

  bool isIndependent{true};

  virtual ~LKernel() {}
};

struct DefaultAAAKernel : LKernel
{
  DefaultAAAKernel(const SP * makerSP): makerSP(makerSP) {}

  VentureValue * simulate(VentureValue * oldVal, const Args & args, gsl_rng * rng) override;
  double weight(VentureValue * newVal, VentureValue * oldVal, const Args & args) override;

  const SP * makerSP;

};

struct DeterministicLKernel : LKernel
{
  DeterministicLKernel(VentureValue * value, SP * sp): value(value), sp(sp) {}

  VentureValue * simulate(VentureValue * oldVal, const Args & args,gsl_rng * rng) override;
  double weight(VentureValue * newVal, VentureValue * oldVal, const Args & args) override;

  VentureValue * value;
  SP * sp;
  
};

struct VariationalLKernel : LKernel
{
  virtual vector<double> gradientOfLogDensity(VentureValue * value,
					      const Args & args) const =0;
  virtual void updateParameters(const vector<double> & gradient,
				double gain, 
				double stepSize) { }
};

struct DefaultVariationalLKernel : VariationalLKernel
{
  DefaultVariationalLKernel(const SP * sp, const Args & args);

  VentureValue * simulate(VentureValue * oldVal, const Args & args,gsl_rng * rng) override;
  double weight(VentureValue * newVal, VentureValue * oldVal, const Args & args) override;

  vector<double> gradientOfLogDensity(VentureValue * value,
				      const Args & args) const override;

  void updateParameters(const vector<double> & gradient, 
			double gain, 
			double stepSize) override;
  const SP * sp;
  vector<double> parameters;
  vector<ParameterScope> parameterScopes;
};

#endif
