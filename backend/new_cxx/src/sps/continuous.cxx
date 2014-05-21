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


/* Normal */
VentureValuePtr NormalPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  checkArgsLength("normal", args, 2);

  double mu = args->operandValues[0]->getDouble();
  double sigma = args->operandValues[1]->getDouble();

  double x = gsl_ran_gaussian(rng, sigma) + mu;

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
  double mu = args->operandValues[0]->getDouble();
  double sigma = args->operandValues[1]->getDouble();
  double x = value->getDouble();

  return NormalDistributionLogLikelihood(x, mu, sigma);
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

VentureValuePtr SimulateLaserPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  checkArgsLength("simulate_laser", args, 2);



  int N_values = 361;
  VentureValuePtr laser_observation(new VentureNil());
  VentureValuePtr laser_range(new VentureNil());
  VentureValuePtr laser_intensity(new VentureNil());
  for(int i=0; i<N_values; i++) {
      double x = gsl_ran_flat(rng, 0.0, 1.0);
      VentureValuePtr vx = shared_ptr<VentureValue>(new VentureNumber(x));
      laser_range = VentureValuePtr(new VenturePair(vx, laser_range));
  }
  for(int i=0; i<N_values; i++) {
      double x = gsl_ran_flat(rng, 0.0, 1.0);
      VentureValuePtr vx = shared_ptr<VentureValue>(new VentureNumber(x));
      laser_intensity = VentureValuePtr(new VenturePair(vx, laser_intensity));
  }
  VentureValuePtr _laser_intensity(new VentureNil());
  _laser_intensity = VentureValuePtr(new VenturePair(laser_intensity, _laser_intensity));
  VentureValuePtr _laser_range(new VentureNil());
  _laser_range = VentureValuePtr(new VenturePair(laser_range, _laser_range));
  laser_observation = VentureValuePtr(new VenturePair(laser_range, laser_observation));
  laser_observation = VentureValuePtr(new VenturePair(laser_intensity, laser_observation));
  return laser_observation;

}

double SimulateLaserPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  return 1.0;
}

double measured_to_vehicle_center(double forward_velocity, double steering_angle,
        double vehicle_h, double vehicle_L) {
    double divisor = 1 - (vehicle_h / vehicle_L) * tan(steering_angle);
    return forward_velocity / divisor;
}

double get_angular_displacement(double dt, double center_velocity,
        double steering_angle, double vehicle_L) {
    return dt * center_velocity / vehicle_L * tan(steering_angle);
}

void get_dx_dy(double dt, double center_velocity, double angular_displacement,
        double heading, double vehicle_a, double vehicle_b,
        double& dx, double& dy) {
    double sin_heading = sin(heading);
    double cos_heading = cos(heading);
    //
    double dx_base = dt * center_velocity * cos_heading;
    double dx_adjustment = -1 * angular_displacement * (vehicle_a * sin_heading + vehicle_b * cos_heading);
    dx = dx_base + dx_adjustment;
    //
    double dy_base = dt * center_velocity * sin_heading;
    double dy_adjustment = angular_displacement * (vehicle_a * cos_heading - vehicle_b * sin_heading);
    dy = dy_base + dy_adjustment;
    return;
}

double normalize_heading(double heading) {
    // FIXME: account for large angle changes?
    // not really, since motion model is probably no good in that regime anyways
    if(heading > M_PI) {
        heading -= 2 * M_PI;
    } else if(heading < -M_PI) {
        heading += 2 * M_PI;
    }
    return heading;
}

void simulate_motion(double dt, vector<VentureValuePtr> pose,
        vector<VentureValuePtr> control, vector<VentureValuePtr> vehicle_params,
        double& dx, double& dy, double& angular_displacement) {
  double heading = pose[2]->getDouble();
  //
  double forward_velocity = control[0]->getDouble();
  double steering_angle = control[1]->getDouble();
  //
  double vehicle_a = vehicle_params[0]->getDouble();
  double vehicle_b = vehicle_params[1]->getDouble();
  double vehicle_h = vehicle_params[2]->getDouble();
  double vehicle_L = vehicle_params[3]->getDouble();


  double center_velocity = measured_to_vehicle_center(forward_velocity,
          steering_angle, vehicle_h, vehicle_L);
  angular_displacement = get_angular_displacement(dt, center_velocity,
          steering_angle, vehicle_L);
  get_dx_dy(dt, center_velocity, angular_displacement, heading,
          vehicle_a, vehicle_b, dx, dy);
  return;
}

double xy_noise_size = .01;
double heading_noise_size = .01;
void add_noise(double& dx, double& dy, double& angular_displacement, gsl_rng * rng) {
  // TODO: better noise model
  double x_noise = 1 + gsl_ran_flat(rng, -xy_noise_size, xy_noise_size);
  double y_noise = 1 + gsl_ran_flat(rng, -xy_noise_size, xy_noise_size);
  double heading_noise = 1 + gsl_ran_flat(rng, -heading_noise_size, heading_noise_size);
  dx *= x_noise;
  dy *= y_noise;
  angular_displacement *= heading_noise;
  return;
}

VentureValuePtr package_new_pose(double x, double y, double heading) {
  VentureValuePtr l(new VentureNil());
  VentureValuePtr vx = shared_ptr<VentureValue>(new VentureNumber(x));
  VentureValuePtr vy = shared_ptr<VentureValue>(new VentureNumber(y));
  VentureValuePtr vheading = shared_ptr<VentureValue>(new VentureNumber(heading));
  l = VentureValuePtr(new VenturePair(vheading, l));
  l = VentureValuePtr(new VenturePair(vy, l));
  l = VentureValuePtr(new VenturePair(vx, l));
  return l;
}

VentureValuePtr update_pose(vector<VentureValuePtr> pose,
        double dx, double dy, double angular_displacement) {
  double x = pose[0]->getDouble() + dx;
  double y = pose[1]->getDouble() + dy;
  double heading = normalize_heading(pose[2]->getDouble() + angular_displacement);
  return package_new_pose(x, y, heading);
}

VentureValuePtr SimulateMotionPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  checkArgsLength("SimulateMotionPSP::simulate", args, 4);
  double dt = args->operandValues[0]->getDouble();
  vector<VentureValuePtr> pose = args->operandValues[1]->getArray();
  vector<VentureValuePtr> control = args->operandValues[2]->getArray();
  vector<VentureValuePtr> vehicle_params = args->operandValues[3]->getArray();

  double dx, dy, angular_displacement;
  simulate_motion(dt, pose, control, vehicle_params, dx, dy, angular_displacement);
  add_noise(dx, dy, angular_displacement, rng);
  return update_pose(pose, dx, dy, angular_displacement);
}

void diff_poses(vector<VentureValuePtr> pose0, vector<VentureValuePtr> pose1,
        double& x_diff, double& y_diff, double& heading_diff) {
    x_diff = pose0[0]->getDouble() - pose1[0]->getDouble();
    y_diff = pose0[1]->getDouble() - pose1[1]->getDouble();
    heading_diff = pose0[2]->getDouble() - pose1[2]->getDouble();
    return;
}

double SimulateMotionPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  checkArgsLength("SimulateMotionPSP::logDensity", args, 4);
  double dt = args->operandValues[0]->getDouble();
  vector<VentureValuePtr> pose = args->operandValues[1]->getArray();
  vector<VentureValuePtr> control = args->operandValues[2]->getArray();
  vector<VentureValuePtr> vehicle_params = args->operandValues[3]->getArray();
  vector<VentureValuePtr> out_pose = value->getArray();

  double x_diff, y_diff, heading_diff;
  diff_poses(pose, out_pose, x_diff, y_diff, heading_diff);
  double dx, dy, angular_displacement;
  simulate_motion(dt, pose, control, vehicle_params, dx, dy, angular_displacement);

  // FIXME: force this to match add_noise
  bool in_x_bound = abs(dx / x_diff - 1) < xy_noise_size;
  bool in_y_bound = abs(dy / y_diff - 1) < heading_noise_size;
  bool in_heading_bound = abs(angular_displacement / heading_diff - 1) < heading_noise_size;
  return in_x_bound * in_y_bound * in_heading_bound;
}

VentureValuePtr SimulateGPSPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  checkArgsLength("SimulateGPSPSP::simulate", args, 1);
  vector<VentureValuePtr> pose = args->operandValues[0]->getArray();

  double dx = gsl_ran_gaussian(rng, 1.0);
  double dy = gsl_ran_gaussian(rng, 1.0);
  double dheading = gsl_ran_gaussian(rng, 0.1);

  return update_pose(pose, dx, dy, dheading);
}

double SimulateGPSPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  checkArgsLength("SimulateGPSPSP::logDensity", args, 1);
  vector<VentureValuePtr> pose = args->operandValues[0]->getArray();
  vector<VentureValuePtr> gps_pose = value->getArray();

  double x_diff, y_diff, heading_diff;
  diff_poses(pose, gps_pose, x_diff, y_diff, heading_diff);
  double x_diff_likelihood = NormalDistributionLogLikelihood(x_diff, 0, 1.0);
  double y_diff_likelihood = NormalDistributionLogLikelihood(y_diff, 0, 1.0);
  double heading_diff_likelihood = NormalDistributionLogLikelihood(heading_diff, 0, 0.1);
  return x_diff_likelihood * y_diff_likelihood * heading_diff_likelihood;
}

VentureValuePtr SimulateMapPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  checkArgsLength("simulate_map", args, 0);

  int num_landmarks = gsl_ran_poisson(rng, 1.0);
  num_landmarks = num_landmarks > 0 ? num_landmarks : 1;

  VentureValuePtr map(new VentureNil());
  for(int i=0; i<num_landmarks; i++) {
      VentureValuePtr landmark(new VentureNil());
      double x = gsl_ran_flat(rng, 0.0, 1.0);
      VentureValuePtr vx = shared_ptr<VentureValue>(new VentureNumber(x));
      double y = gsl_ran_flat(rng, 0.0, 1.0);
      VentureValuePtr vy = shared_ptr<VentureValue>(new VentureNumber(y));
      landmark = VentureValuePtr(new VenturePair(vx, landmark));
      landmark = VentureValuePtr(new VenturePair(vy, landmark));
      map = VentureValuePtr(new VenturePair(landmark, map));
  }
  return map;
}

double SimulateMapPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  return 1.0;
}

/* Gamma */
VentureValuePtr GammaPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  checkArgsLength("gamma", args, 2);

  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();

  double x = gsl_ran_gamma(rng, a, 1.0 / b);
  return VentureValuePtr(new VentureNumber(x));
}

double GammaPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();
  double x = value->getDouble();
  return GammaDistributionLogLikelihood(x, a, b);
}

/* Inv Gamma */
VentureValuePtr InvGammaPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  checkArgsLength("inv_gamma", args, 2);

  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();

  double x = 1.0 / gsl_ran_gamma(rng, a, 1.0 / b);
  return VentureValuePtr(new VentureNumber(x));
}

double InvGammaPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();
  double x = value->getDouble();
  return InvGammaDistributionLogLikelihood(x, a, b);
}

/* UniformContinuous */
VentureValuePtr UniformContinuousPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  checkArgsLength("uniform_continuous", args, 2);

  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();
  
  double x = gsl_ran_flat(rng,a,b);
  return VentureValuePtr(new VentureNumber(x));
}

double UniformContinuousPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();
  double x = value->getDouble();
  return log(gsl_ran_flat_pdf(x,a,b));
}

/* Beta */
VentureValuePtr BetaPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  checkArgsLength("beta", args, 2);

  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();
  
  double x = gsl_ran_beta(rng,a,b);
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
  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();
  double x = value->getDouble();
  return BetaDistributionLogLikelihood(x, a, b);
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
//  checkArgsLength("student_t", args, 1);

  double nu = args->operandValues[0]->getDouble();
  double loc = 0; if (args->operandValues.size() > 1) { loc = args->operandValues[1]->getDouble(); }
  double shape = 1; if (args->operandValues.size() > 2) { shape = args->operandValues[2]->getDouble(); }
  
  double x = gsl_ran_tdist(rng,nu);
  return VentureValuePtr(new VentureNumber((shape * x) + loc));
}

double StudentTPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  double nu = args->operandValues[0]->getDouble();
  double loc = 0; if (args->operandValues.size() > 1) { loc = args->operandValues[1]->getDouble(); }
  double shape = 1; if (args->operandValues.size() > 2) { shape = args->operandValues[2]->getDouble(); }

  double x = value->getDouble();
  double y = (x - loc) / shape;
  // TODO: compute in logspace
  return log(gsl_ran_tdist_pdf(y,nu) / shape);
}

VentureValuePtr ChiSquaredPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("chi_sq", args, 1);

  double nu = args->operandValues[0]->getDouble();
  
  double x = gsl_ran_chisq(rng,nu);
  return VentureValuePtr(new VentureNumber(x));
}
 
double ChiSquaredPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  double nu = args->operandValues[0]->getDouble();
  double x = value->getDouble();
  return ChiSquaredDistributionLogLikelihood(x,nu);
}

VentureValuePtr InvChiSquaredPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("inv_chi_sq", args, 1);

  double nu = args->operandValues[0]->getDouble();
  
  double x = 1.0 / gsl_ran_chisq(rng,nu);
  return VentureValuePtr(new VentureNumber(x));
}
 
double InvChiSquaredPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  double nu = args->operandValues[0]->getDouble();
  double x = value->getDouble();
  return InvChiSquaredDistributionLogLikelihood(x,nu);
}
