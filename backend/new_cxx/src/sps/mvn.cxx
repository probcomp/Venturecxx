// Copyright (c) 2013, MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

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

/* TODO we continually convert back and forth from Eigen to GSL here. It is ridiculous!
   We have two options: change the code to sample directly to use Eigen instead of GSL,
   or change Eigen to GSL everywhere. */

VentureValuePtr MVNormalPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  checkArgsLength("normal", args, 2);

  VectorXd mu = args->operandValues[0]->getVector();
  int n = mu.size(); // size may be wrong
  shared_ptr<gsl_vector> gsl_mu(gsl_vector_alloc(n)); 
  for (int i = 0; i < n; ++i) { gsl_vector_set(gsl_mu.get(),i,mu(i)); }

  MatrixXd sigma = args->operandValues[1]->getSymmetricMatrix();
  shared_ptr<gsl_matrix> gsl_sigma(gsl_matrix_alloc(n,n));
  for (int i = 0; i < n; ++i) {
    for (int j = 0; j < n; ++j) { 
      gsl_matrix_set(gsl_sigma.get(),i,j,sigma(i,j));
    }
  }

  shared_ptr<gsl_vector> gsl_x(gsl_vector_alloc(n)); // output
  
  rmvnorm(rng, n, gsl_mu.get(), gsl_sigma.get(), gsl_x.get());

  VectorXd x(n);
  for (int i = 0; i < n; ++i) { x(i) = gsl_vector_get(gsl_x.get(),i); }

  return VentureValuePtr(new VentureVector(x));
}


double MVNormalPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  VectorXd mu = args->operandValues[0]->getVector();
  int n = mu.size(); // size may be wrong
  shared_ptr<gsl_vector> gsl_mu(gsl_vector_alloc(n)); 
  for (int i = 0; i < n; ++i) { gsl_vector_set(gsl_mu.get(),i,mu(i)); }

  MatrixXd sigma = args->operandValues[1]->getMatrix();
  shared_ptr<gsl_matrix> gsl_sigma(gsl_matrix_alloc(n,n));
  for (int i = 0; i < n; ++i) {
    for (int j = 0; j < n; ++j) { 
      gsl_matrix_set(gsl_sigma.get(),i,j,sigma(i,j));
    }
  }

  shared_ptr<gsl_vector> gsl_x(gsl_vector_alloc(n)); // output
  VectorXd x = value->getVector();
  for (int i = 0; i < n; ++i) { gsl_vector_set(gsl_x.get(),i,x[i]); }

  return dmvnorm(n, gsl_x.get(), gsl_mu.get(), gsl_sigma.get());
}

