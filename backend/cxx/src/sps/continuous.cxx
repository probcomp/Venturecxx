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
  VentureDouble * vmu = dynamic_cast<VentureDouble *>(operands[0]->getValue());
  if (vmu) { mu = vmu->x; }
  else 
  {
    VentureCount * vcmu = dynamic_cast<VentureCount*>(operands[0]->getValue());
    assert(vcmu);
    mu = vcmu->n;
  }

  VentureDouble * sigma = dynamic_cast<VentureDouble *>(operands[1]->getValue());

  assert(sigma);
  double x = gsl_ran_gaussian(rng, sigma->x) + mu;
  return new VentureDouble(x);
}

double NormalSP::logDensityOutput(VentureValue * value, Node * node)  const
{
  vector<Node *> & operands = node->operandNodes;
  double mu;
  VentureDouble * vmu = dynamic_cast<VentureDouble *>(operands[0]->getValue());
  if (vmu) { mu = vmu->x; }
  else 
  {
    VentureCount * vcmu = dynamic_cast<VentureCount*>(operands[0]->getValue());
    assert(vcmu);
    mu = vcmu->n;
  }

  VentureDouble * sigma = dynamic_cast<VentureDouble *>(operands[1]->getValue());
  VentureDouble * x = dynamic_cast<VentureDouble *>(value);
  assert(sigma);
  assert(x);
  return log(gsl_ran_gaussian_pdf(x->x - mu, sigma->x));
}

/* Gamma */
VentureValue * GammaSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureDouble * a = dynamic_cast<VentureDouble *>(operands[0]->getValue());
  VentureDouble * b = dynamic_cast<VentureDouble *>(operands[1]->getValue());
  assert(a);
  assert(b);
  double x = gsl_ran_gamma(rng, a->x, b->x);
  return new VentureDouble(x);
}

double GammaSP::logDensityOutput(VentureValue * value, Node * node)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureDouble * a = dynamic_cast<VentureDouble *>(operands[0]->getValue());
  VentureDouble * b = dynamic_cast<VentureDouble *>(operands[1]->getValue());
  VentureDouble * x = dynamic_cast<VentureDouble *>(value);
  assert(a);
  assert(b);
  assert(x);
  return log(gsl_ran_gamma_pdf(x->x, a->x, b->x));
}


/* UniformContinuous */
VentureValue * UniformContinuousSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureDouble * a = dynamic_cast<VentureDouble *>(operands[0]->getValue());
  VentureDouble * b = dynamic_cast<VentureDouble *>(operands[1]->getValue());
  assert(a);
  assert(b);
  double x = gsl_ran_flat(rng,a->x,b->x);
  return new VentureDouble(x);
}

double UniformContinuousSP::logDensityOutput(VentureValue * value, Node * node)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureDouble * a = dynamic_cast<VentureDouble *>(operands[0]->getValue());
  VentureDouble * b = dynamic_cast<VentureDouble *>(operands[1]->getValue());
  VentureDouble * x = dynamic_cast<VentureDouble *>(value);
  assert(a);
  assert(b);
  assert(x);
  return log(gsl_ran_flat_pdf(x->x,a->x,b->x));
}

