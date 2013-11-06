#include "node.h"
#include "sp.h"
#include "sps/continuous.h"
#include "value.h"

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

#include <cmath>
#include <vector>

#include <cassert>
#include <iostream>

/* Normal */
VentureValue * NormalSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  double mu;
  VentureNumber * vmu = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  if (vmu) { mu = vmu->x; }
  else 
  {
    VentureAtom * vcmu = dynamic_cast<VentureAtom*>(operands[0]->getValue());
    assert(vcmu);
    mu = vcmu->n;
  }

  VentureNumber * sigma = dynamic_cast<VentureNumber *>(operands[1]->getValue());

  assert(sigma);
  double x = gsl_ran_gaussian(rng, sigma->x) + mu;
  return new VentureNumber(x);
}

double NormalSP::logDensityOutput(VentureValue * value, Node * node)  const
{
  vector<Node *> & operands = node->operandNodes;
  double mu;
  VentureNumber * vmu = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  if (vmu) { mu = vmu->x; }
  else 
  {
    VentureAtom * vcmu = dynamic_cast<VentureAtom*>(operands[0]->getValue());
    assert(vcmu);
    mu = vcmu->n;
  }

  VentureNumber * sigma = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  VentureNumber * x = dynamic_cast<VentureNumber *>(value);
  assert(sigma);
  assert(x);
  return log(gsl_ran_gaussian_pdf(x->x - mu, sigma->x));
}

/* Gamma */
VentureValue * GammaSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * a = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * b = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  assert(a);
  assert(b);
  double x = gsl_ran_gamma(rng, a->x, b->x);
  return new VentureNumber(x);
}

double GammaSP::logDensityOutput(VentureValue * value, Node * node)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * a = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * b = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  VentureNumber * x = dynamic_cast<VentureNumber *>(value);
  assert(a);
  assert(b);
  assert(x);
  return log(gsl_ran_gamma_pdf(x->x, a->x, b->x));
}


/* UniformContinuous */
VentureValue * UniformContinuousSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * a = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * b = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  assert(a);
  assert(b);
  double x = gsl_ran_flat(rng,a->x,b->x);
  return new VentureNumber(x);
}

double UniformContinuousSP::logDensityOutput(VentureValue * value, Node * node)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * a = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * b = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  VentureNumber * x = dynamic_cast<VentureNumber *>(value);
  assert(a);
  assert(b);
  assert(x);
  return log(gsl_ran_flat_pdf(x->x,a->x,b->x));
}

/* Beta */
VentureValue * BetaSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * a = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * b = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  assert(a);
  assert(b);
  double x = gsl_ran_beta(rng,a->x,b->x);
  return new VentureNumber(x);
}

double BetaSP::logDensityOutput(VentureValue * value, Node * node)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * a = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * b = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  VentureNumber * x = dynamic_cast<VentureNumber *>(value);
  assert(a);
  assert(b);
  assert(x);
  return log(gsl_ran_beta_pdf(x->x,a->x,b->x));
}

/* Student-t */
VentureValue * StudentTSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * nu = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  assert(nu);
  double x = gsl_ran_tdist(rng,nu->x);
  return new VentureNumber(x);
}

double StudentTSP::logDensityOutput(VentureValue * value, Node * node)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * nu = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * x = dynamic_cast<VentureNumber *>(value);
  assert(nu);
  assert(x);
  return log(gsl_ran_tdist_pdf(x->x,nu->x));
}
