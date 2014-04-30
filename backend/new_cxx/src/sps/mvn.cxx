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
#include "sps/mvn.h"
#include "sps/silva_mvn.h"
#include "sps/numerical_helpers.h"
#include "args.h"
#include "values.h"
#include "utils.h"

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include <gsl/gsl_sf.h>
#include <cmath>
#include <cfloat>

using std::isfinite;

VentureValuePtr MVNormalPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  checkArgsLength("normal", args, 2);
  MatrixXd mu = args->operandValues[0]->getVector(); // Matrix?
  MatrixXd sigma = args->operandValues[1]->getMatrix();
  gsl_vector * x = gsl_vector_alloc(n);
  
  rmvnorm(rng, mu., const gsl_vector *mean, const gsl_matrix *var, gsl_vector *result){

  return VentureValuePtr(new VentureNumber(x));
}

double MVNormalPSP::simulateNumeric(const vector<double> & args, gsl_rng * rng)  const
{
  double x = gsl_ran_gaussian(rng, args[1]) + args[0];
  if (!isfinite(x))
  {
    cout << "Normal(" << args[0] << ", " << args[1] << ") = " << x << endl;
  }
  assert(isfinite(x));
  return x;
}

double MVNormalPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  double mu = args->operandValues[0]->getDouble();
  double sigma = args->operandValues[1]->getDouble();
  double x = value->getDouble();

  return NormalDistributionLogLikelihood(x, mu, sigma);
}

double MVNormalPSP::logDensityNumeric(double output, const vector<double> & args) const
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
