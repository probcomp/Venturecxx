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
      name = "normal";
    }

  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
  double simulateOutputNumeric(const vector<double> & args, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, const Args & args) const override;

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
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, const Args & args) const override;
};

struct InvGammaSP : SP
{
  InvGammaSP()
    {
      isRandomOutput = true;
      canAbsorbOutput = true;
    }
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, const Args & args) const override;
};

struct UniformContinuousSP : SP
{
  UniformContinuousSP()
    {
      isRandomOutput = true;
      canAbsorbOutput = true;
    }

  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, const Args & args) const override;
};

struct BetaSP : SP
{
  BetaSP()
    {
      isRandomOutput = true;
      canAbsorbOutput = true;
      hasVariationalLKernel = true;
      name = "beta";
    }

  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
  double simulateOutputNumeric(const vector<double> & args, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, const Args & args) const override;

  double logDensityOutputNumeric(double output, const vector<double> & args) const override;

  vector<ParameterScope> getParameterScopes() const override;
  vector<double> gradientOfLogDensity(double output,
				      const vector<double> & arguments) const override;
};

struct StudentTSP : SP
{
  StudentTSP()
    {
      isRandomOutput = true;
      canAbsorbOutput = true;
    }

  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, const Args & args) const override;
};


struct ChiSquareSP : SP
{
  ChiSquareSP()
    {
      isRandomOutput = true;
      canAbsorbOutput = true;
    }

  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, const Args & args) const override;
};

struct InverseChiSquareSP : SP
{
  InverseChiSquareSP()
    {
      isRandomOutput = true;
      canAbsorbOutput = true;
    }

  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, const Args & args) const override;
};


#endif
