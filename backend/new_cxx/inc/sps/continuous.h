#ifndef CONTINUOUS_SPS_H
#define CONTINUOUS_SPS_H

#include "psp.h"

/* Continuous scalar random SPs. */
struct NormalPSP : RandomPSP
{

  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;
  
  double simulateNumeric(const vector<double> & args, gsl_rng * rng) const;
  double logDensityNumeric(double , const vector<double> & args) const;

  //vector<ParameterScope> getParameterScopes() const;
  vector<double> gradientOfLogDensity(double ,
				      const vector<double> & arguments) const;

};

struct GammaPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;
};

struct InvGammaPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;
};

struct UniformContinuousPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;
};

struct BetaPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double simulateNumeric(const vector<double> & args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;

  double logDensityNumeric(double , const vector<double> & args) const;

  //vector<ParameterScope> getParameterScopes() const;
  vector<double> gradientOfLogDensity(double ,
				      const vector<double> & arguments) const;
};

struct StudentTPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;
};


struct ChiSquaredPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;
};

struct InvChiSquaredPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;
};


#endif
