#ifndef CONTINUOUS_SPS_H
#define CONTINUOUS_SPS_H

#include "sp.h"

// /* Continuous scalar random SPs. */
// struct MVNormalSP : SP {
//   MVNormalSP() : SP("mvnormal") {
//     isRandomOutput = true;
//     canAbsorbOutput = true;
//     hasVariationalLKernel = true;
//   }

//   VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
//   double simulateOutputNumeric(const vector<double> & args, gsl_rng * rng) const override;
//   double logDensityOutput(VentureValue * value, Node * node) const override;

//   double logDensityOutputNumeric(double output, const vector<double> & args) const override;

//   vector<ParameterScope> getParameterScopes() const override;
//   vector<double> gradientOfLogDensity(double output,
//               const vector<double> & arguments) const override;
// };


struct NormalSP : SP
{
  NormalSP(): SP("normal")
    {
      isRandomOutput = true;
      canAbsorbOutput = true;
      hasVariationalLKernel = true;
    }

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  double simulateOutputNumeric(const vector<double> & args, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, Node * node) const override;

  double logDensityOutputNumeric(double output, const vector<double> & args) const override;

  vector<ParameterScope> getParameterScopes() const override;
  vector<double> gradientOfLogDensity(double output,
				      const vector<double> & arguments) const override;

};

struct GammaSP : SP
{
  GammaSP(): SP("gamma")
    {
      isRandomOutput = true;
      canAbsorbOutput = true;
    }
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, Node * node) const override;
};

struct InvGammaSP : SP
{
  InvGammaSP(): SP("inv_gamma")
    {
      isRandomOutput = true;
      canAbsorbOutput = true;
    }
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, Node * node) const override;
};

struct UniformContinuousSP : SP
{
  UniformContinuousSP(): SP("uniform_continuous")
    {
      isRandomOutput = true;
      canAbsorbOutput = true;
    }

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, Node * node) const override;
};

struct BetaSP : SP
{
  BetaSP(): SP("beta")
    {
      isRandomOutput = true;
      canAbsorbOutput = true;
      hasVariationalLKernel = true;
      name = "beta";
    }

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  double simulateOutputNumeric(const vector<double> & args, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, Node * node) const override;

  double logDensityOutputNumeric(double output, const vector<double> & args) const override;

  vector<ParameterScope> getParameterScopes() const override;
  vector<double> gradientOfLogDensity(double output,
				      const vector<double> & arguments) const override;
};

struct StudentTSP : SP
{
  StudentTSP(): SP("student_t")
    {
      isRandomOutput = true;
      canAbsorbOutput = true;
    }

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, Node * node) const override;
};


struct ChiSquareSP : SP
{
  ChiSquareSP(): SP("chi_sq")
    {
      isRandomOutput = true;
      canAbsorbOutput = true;
    }

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, Node * node) const override;
};

struct InverseChiSquareSP : SP
{
  InverseChiSquareSP(): SP("inv_chi_sq")
    {
      isRandomOutput = true;
      canAbsorbOutput = true;
    }

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, Node * node) const override;
};


#endif
