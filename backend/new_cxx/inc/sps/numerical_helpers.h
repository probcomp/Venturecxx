// Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

#ifndef SPS_NUMERICAL_HELPERS_H
#define SPS_NUMERICAL_HELPERS_H

double NormalDistributionLogLikelihood(double sampled_value, double average, double sigma);
double GammaDistributionLogLikelihood(double sampled_value, double alpha, double beta);
double InvGammaDistributionLogLikelihood(double sampled_value, double alpha, double beta);
double ExponentialDistributionLogLikelihood(double sampled_value, double theta);
double BetaDistributionLogLikelihood(double sampled_value, double alpha, double beta);
double ChiSquaredDistributionLogLikelihood(double sampled_value, double nu);
double InvChiSquaredDistributionLogLikelihood(double sampled_value, double nu);
double PoissonDistributionLogLikelihood(int sampled_value_count, double lambda);
#endif
