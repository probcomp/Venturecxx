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

  bool isContinuous() const { return true; }


};

struct GammaPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;

  bool isContinuous() const { return true; }
  double getSupportLowerBound() const { return 0; }

};

struct InvGammaPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;

  bool isContinuous() const { return true; }
  double getSupportLowerBound() const { return 0; }

};

struct ExponentialPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;

  bool isContinuous() const { return true; }
  double getSupportLowerBound() const { return 0; }

};

struct UniformContinuousPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;

  bool isContinuous() const { return true; }
  // TODO Upper and lower bounds really depend on the arguments
  // Defaulting to permissive for now.
  // double getSupportLowerBound() const { return 0; }
  // double getSupportUpperBound() const { return 1; }

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

  bool isContinuous() const { return true; }
  double getSupportLowerBound() const { return 0; }
  double getSupportUpperBound() const { return 1; }

};

struct StudentTPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;

  bool isContinuous() const { return true; }

};


struct ChiSquaredPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;

  bool isContinuous() const { return true; }
  double getSupportLowerBound() const { return 0; }

};

struct InvChiSquaredPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;

  bool isContinuous() const { return true; }
  double getSupportLowerBound() const { return 0; }

};

struct ApproximateBinomialPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;

  bool isContinuous() const { return true; }
  double getSupportLowerBound() const { return 0; }

};

#endif
