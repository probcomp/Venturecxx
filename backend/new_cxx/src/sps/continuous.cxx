/*
* Copyright (c) 2013, MIT Probabilistic Computing Project.
* 
* This file is part of Venture.
* 
* Venture is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
* 
* Venture is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
* 
* You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
*/
#include "sps/continuous.h"
#include "args.h"
#include "values.h"

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include <gsl/gsl_sf.h>
#include <cmath>
#include <cfloat>

using std::isfinite;


/* Normal */
VentureValuePtr NormalPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  vector<VentureValuePtr> & operands = args->operandValues;

  shared_ptr<VentureNumber> vmu = dynamic_pointer_cast<VentureNumber>(operands[0]);
  shared_ptr<VentureNumber> vsigma = dynamic_pointer_cast<VentureNumber>(operands[1]);
  assert(vmu);
  assert(vsigma);
  double x = gsl_ran_gaussian(rng, vsigma->getDouble()) + vmu->getDouble();
//  cout << "Normal::simulate(" << x << " | " << vmu->getDouble() << ", " << vsigma->getDouble() << ")" << endl;
  return VentureValuePtr(new VentureNumber(x));
}

double NormalPSP::simulateNumeric(const vector<double> & args, gsl_rng * rng)  const
{
  double x = gsl_ran_gaussian(rng, args[1]) + args[0];
  if (!isfinite(x))
  {
    cout << "Normal(" << args[0] << ", " << args[1] << ") = " << x << endl;
  }
  assert(isfinite(x));
  return x;
}

double NormalPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  vector<VentureValuePtr> & operands = args->operandValues;
  double mu;
  shared_ptr<VentureNumber> vmu = dynamic_pointer_cast<VentureNumber>(operands[0]);
  if (vmu) { mu = vmu->getDouble(); }
  else
  {
    shared_ptr<VentureAtom> vcmu = dynamic_pointer_cast<VentureAtom>(operands[0]);
    assert(vcmu);
    mu = vcmu->n;
  }

  shared_ptr<VentureNumber> sigma = dynamic_pointer_cast<VentureNumber>(operands[1]);
  shared_ptr<VentureNumber> x = dynamic_pointer_cast<VentureNumber>(value);
  assert(sigma);
  assert(x);
//  cout << "Normal::logDensity(" << x->getDouble() << " | " << mu << ", " << sigma->getDouble() << ")" << endl;
  return NormalDistributionLogLikelihood(x->getDouble(), mu, sigma->getDouble());
}

double NormalPSP::logDensityNumeric(double output, const vector<double> & args) const
{
  assert(isfinite(args[0]));
  assert(isfinite(args[1]));
  assert(isfinite(output));
  assert(args[1] > 0);
  double ld = NormalDistributionLogLikelihood(output, args[0], args[1]);
  if (!isfinite(ld))
  {
    cout << "Normal(" << args[0] << ", " << args[1] << ") = " << output << " <" << ld << ">" << endl;
  }
  assert(isfinite(ld));
  return ld;
}

/*
vector<ParameterScope> NormalPSP::getParameterScopes() const
{
  return {ParameterScope::REAL, ParameterScope::POSITIVE_REAL};
}
*/

vector<double> NormalPSP::gradientOfLogDensity(double output,
					      const vector<double> & arguments) const
{
  double mu = arguments[0];
  double sigma = arguments[1];
  double x = output;

  double gradMu = (x - mu) / (sigma * sigma);
  double gradSigma = (((x - mu) * (x - mu)) - (sigma * sigma)) / (sigma * sigma * sigma);
  
  vector<double> ret;
  ret.push_back(gradMu);
  ret.push_back(gradSigma);
  return ret;
}

/* Gamma */
VentureValuePtr GammaPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  vector<VentureValuePtr> & operands = args->operandValues;
  shared_ptr<VentureNumber> a = dynamic_pointer_cast<VentureNumber>(operands[0]);
  shared_ptr<VentureNumber> b = dynamic_pointer_cast<VentureNumber>(operands[1]);
  assert(a);
  assert(b);
  double x = gsl_ran_gamma(rng, a->getDouble(), 1.0 / b->getDouble());
  return VentureValuePtr(new VentureNumber(x));
}

double GammaPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  vector<VentureValuePtr> & operands = args->operandValues;
  shared_ptr<VentureNumber> a = dynamic_pointer_cast<VentureNumber>(operands[0]);
  shared_ptr<VentureNumber> b = dynamic_pointer_cast<VentureNumber>(operands[1]);
  shared_ptr<VentureNumber> x = dynamic_pointer_cast<VentureNumber>(value);
  assert(a);
  assert(b);
  assert(x);
  return GammaDistributionLogLikelihood(x->getDouble(), a->getDouble(), b->getDouble());
}

/* Inv Gamma */
VentureValuePtr InvGammaPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  vector<VentureValuePtr> & operands = args->operandValues;
  shared_ptr<VentureNumber> a = dynamic_pointer_cast<VentureNumber>(operands[0]);
  shared_ptr<VentureNumber> b = dynamic_pointer_cast<VentureNumber>(operands[1]);
  assert(a);
  assert(b);
  double x = 1.0 / gsl_ran_gamma(rng, a->getDouble(), 1.0 / b->getDouble());
  return VentureValuePtr(new VentureNumber(x));
}

double InvGammaPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  vector<VentureValuePtr> & operands = args->operandValues;
  shared_ptr<VentureNumber> a = dynamic_pointer_cast<VentureNumber>(operands[0]);
  shared_ptr<VentureNumber> b = dynamic_pointer_cast<VentureNumber>(operands[1]);
  shared_ptr<VentureNumber> x = dynamic_pointer_cast<VentureNumber>(value);
  assert(a);
  assert(b);
  assert(x);
  return InvGammaDistributionLogLikelihood(x->getDouble(), a->getDouble(), b->getDouble());
}

/* UniformContinuous */
VentureValuePtr UniformContinuousPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  vector<VentureValuePtr> & operands = args->operandValues;
  shared_ptr<VentureNumber> a = dynamic_pointer_cast<VentureNumber>(operands[0]);
  shared_ptr<VentureNumber> b = dynamic_pointer_cast<VentureNumber>(operands[1]);
  assert(a);
  assert(b);
  double x = gsl_ran_flat(rng,a->getDouble(),b->getDouble());
  return VentureValuePtr(new VentureNumber(x));
}

double UniformContinuousPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  vector<VentureValuePtr> & operands = args->operandValues;
  shared_ptr<VentureNumber> a = dynamic_pointer_cast<VentureNumber>(operands[0]);
  shared_ptr<VentureNumber> b = dynamic_pointer_cast<VentureNumber>(operands[1]);
  shared_ptr<VentureNumber> x = dynamic_pointer_cast<VentureNumber>(value);
  assert(a);
  assert(b);
  assert(x);
  return log(gsl_ran_flat_pdf(x->getDouble(),a->getDouble(),b->getDouble()));
}

/* Beta */
VentureValuePtr BetaPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  vector<VentureValuePtr> & operands = args->operandValues;
  shared_ptr<VentureNumber> a = dynamic_pointer_cast<VentureNumber>(operands[0]);
  shared_ptr<VentureNumber> b = dynamic_pointer_cast<VentureNumber>(operands[1]);
  assert(a);
  assert(b);
  double x = gsl_ran_beta(rng,a->getDouble(),b->getDouble());
  if (x > .99) { x = 0.99; }
  if (x < 0.01) { x = 0.01; }

  return VentureValuePtr(new VentureNumber(x));
}

double BetaPSP::simulateNumeric(const vector<double> & args, gsl_rng * rng) const
{
  assert(args[0] > 0);
  assert(args[1] > 0);
  double x = gsl_ran_beta(rng,args[0],args[1]);
  assert(isfinite(x));
  // TODO FIXME GSL NUMERIC
  if (x > .99) { x = 0.99; }
  if (x < 0.01) { x = 0.01; }
  return x;
}

double BetaPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  vector<VentureValuePtr> & operands = args->operandValues;
  shared_ptr<VentureNumber> a = dynamic_pointer_cast<VentureNumber>(operands[0]);
  shared_ptr<VentureNumber> b = dynamic_pointer_cast<VentureNumber>(operands[1]);
  shared_ptr<VentureNumber> x = dynamic_pointer_cast<VentureNumber>(value);
  assert(a);
  assert(b);
  assert(x);
  return BetaDistributionLogLikelihood(x->getDouble(), a->getDouble(), b->getDouble());
}

double BetaPSP::logDensityNumeric(double output, const vector<double> & args) const
{
  assert(args[0] > 0);
  assert(args[1] > 0);
  assert(0 <= output);
  assert(output <= 1);
  double ld = BetaDistributionLogLikelihood(output, args[0], args[1]);
  if (!isfinite(ld))
  {
    cout << "Beta(" << args[0] << ", " << args[1] << ") = " << output << " <" << ld << ">" << endl;
  }

  assert(isfinite(ld));
  return ld;
}

/*
vector<ParameterScope> BetaPSP::getParameterScopes() const
{
  return {ParameterScope::POSITIVE_REAL, ParameterScope::POSITIVE_REAL};
}
*/

vector<double> BetaPSP::gradientOfLogDensity(double output,
					      const vector<double> & arguments) const
{
  double a = arguments[0];
  double b = arguments[1];

  double alpha0 = a + b;

  double gradA = log(output) + gsl_sf_psi(alpha0) - gsl_sf_psi(a);
  double gradB = log(output) + gsl_sf_psi(alpha0) - gsl_sf_psi(b);

  assert(isfinite(gradA));
  assert(isfinite(gradB));
  
  vector<double> ret;
  ret.push_back(gradA);
  ret.push_back(gradB);
  return ret;

}

/* Student-t */
VentureValuePtr StudentTPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  vector<VentureValuePtr> & operands = args->operandValues;
  shared_ptr<VentureNumber> nu = dynamic_pointer_cast<VentureNumber>(operands[0]);
  assert(nu);
  double x = gsl_ran_tdist(rng,nu->getDouble());
  return VentureValuePtr(new VentureNumber(x));
}

double StudentTPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  vector<VentureValuePtr> & operands = args->operandValues;
  shared_ptr<VentureNumber> nu = dynamic_pointer_cast<VentureNumber>(operands[0]);
  shared_ptr<VentureNumber> x = dynamic_pointer_cast<VentureNumber>(value);
  assert(nu);
  assert(x);
  return log(gsl_ran_tdist_pdf(x->getDouble(),nu->getDouble()));
}

VentureValuePtr ChiSquaredPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  vector<VentureValuePtr> & operands = args->operandValues;
  shared_ptr<VentureNumber> nu = dynamic_pointer_cast<VentureNumber>(operands[0]);
  assert(nu);
  return VentureValuePtr(new VentureNumber(gsl_ran_chisq(rng,nu->getDouble())));
}
 
double ChiSquaredPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  vector<VentureValuePtr> & operands = args->operandValues;
  shared_ptr<VentureNumber> nu = dynamic_pointer_cast<VentureNumber>(operands[0]);
  shared_ptr<VentureNumber> x = dynamic_pointer_cast<VentureNumber>(value);
  assert(nu);
  assert(x);
  return ChiSquaredDistributionLogLikelihood(x->getDouble(),nu->getDouble());
}

VentureValuePtr InvChiSquaredPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  vector<VentureValuePtr> & operands = args->operandValues;
  shared_ptr<VentureNumber> nu = dynamic_pointer_cast<VentureNumber>(operands[0]);
  assert(nu);
  return VentureValuePtr(new VentureNumber(1.0 / gsl_ran_chisq(rng,nu->getDouble())));
}
 
double InvChiSquaredPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  vector<VentureValuePtr> & operands = args->operandValues;
  shared_ptr<VentureNumber> nu = dynamic_pointer_cast<VentureNumber>(operands[0]);
  shared_ptr<VentureNumber> x = dynamic_pointer_cast<VentureNumber>(value);
  assert(nu);
  assert(x);
  return InvChiSquaredDistributionLogLikelihood(x->getDouble(),nu->getDouble());
}
