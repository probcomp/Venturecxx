#ifndef CONTINUOUS_SPS_H
#define CONTINUOUS_SPS_H

#include "sp.h"

/* Continuous scalar random SPs. */
struct NormalSP : SP
{ 
  NormalSP()
    { 
      isRandomOutput = true;
      canAbsorbOutput = true;
      hasVariationalLKernel = true;
    }

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
  double logDensityOutput(VentureValue * value, Node * node) const override; 

  double logDensityOutputNumeric(double output, const vector<double> & args) const override;

  vector<ParameterScope> getParameterScopes() const override;
  vector<double> gradientOfLogDensity(double output,
				      const vector<double> & arguments) const override;

};

struct GammaSP : SP
{ 
  GammaSP()
    { 
      isRandomOutput = true;
      canAbsorbOutput = true;
    }
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
  double logDensityOutput(VentureValue * value, Node * node) const override; 
};

struct UniformContinuousSP : SP
{ 
  UniformContinuousSP()
    { 
      isRandomOutput = true;
      canAbsorbOutput = true;
    }

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
  double logDensityOutput(VentureValue * value, Node * node) const override; 
};

struct BetaSP : SP
{ 
  BetaSP()
    { 
      isRandomOutput = true;
      canAbsorbOutput = true;
      hasVariationalLKernel = true;
    }

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
  double logDensityOutput(VentureValue * value, Node * node) const override; 

  double logDensityOutputNumeric(double output, const vector<double> & args) const override;

  vector<ParameterScope> getParameterScopes() const override;
  vector<double> gradientOfLogDensity(double output,
				      const vector<double> & arguments) const override;

};

#endif
