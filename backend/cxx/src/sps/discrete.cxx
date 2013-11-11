#include "node.h"
#include "sp.h"
#include "sps/discrete.h"
#include "value.h"
#include "utils.h"

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include <gsl/gsl_sf.h>

#include <iostream>
#include <vector>

//LogLikelihoods, from Yura's Utilities.cpp
double PoissonDistributionLogLikelihood(int sampled_value_count, double lambda) {
  //l^k * e^{-l} / k!
  double loglikelihood = sampled_value_count * log(lambda);
  loglikelihood -= gsl_sf_lnfact(sampled_value_count);
  loglikelihood -= lambda;
  return loglikelihood;
}


/* Bernoulli */

VentureValue * BernoulliSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  double p = 0.5;
  if (!operands.empty())
  {
    VentureNumber * vp = dynamic_cast<VentureNumber *>(operands[0]->getValue());
    assert(vp);
    assert(vp->x >= 0 && vp->x <= 1);
    p = vp->x;
  }
  uint32_t n = gsl_ran_bernoulli(rng,p);
  assert(n == 0 || n == 1);
  return new VentureBool(n);
} 

double BernoulliSP::logDensityOutput(VentureValue * value, Node * node) const
{
  vector<Node *> & operands = node->operandNodes;
  VentureBool * b = dynamic_cast<VentureBool *>(value);
  assert(b);

  double p = 0.5;
  if (!operands.empty())
  {
    VentureNumber * vp = dynamic_cast<VentureNumber *>(operands[0]->getValue());
    assert(vp);
    assert(vp->x >= 0 && vp->x <= 1);
    p = vp->x;
  }

  if (b->pred) { return log(p); }
  else { return log(1 - p); }
}

vector<VentureValue*> BernoulliSP::enumerateOutput(Node * node) const
{
  VentureBool * vold = dynamic_cast<VentureBool*>(node->getValue());
  assert(vold);

  double p = 0.5;
  if (!node->operandNodes.empty())
  {
    VentureNumber * vp = dynamic_cast<VentureNumber *>(node->operandNodes[0]->getValue());
    assert(vp);
    assert(vp->x >= 0 && vp->x <= 1);
    p = vp->x;
  }

  vector<VentureValue *> vals;
  if (vold->pred && p < 1) { vals.push_back(new VentureBool(false)); }
  else if (!vold->pred && p > 0) { vals.push_back(new VentureBool(true)); }

  return vals;
}

/* Categorical */
VentureValue * CategoricalSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<double> ps;
  for (Node * operandNode : node->operandNodes)
  {
    VentureNumber * d = dynamic_cast<VentureNumber *>(operandNode->getValue());
    assert(d);
    ps.push_back(d->x);
  }
  normalizeVector(ps);

  double u = gsl_ran_flat(rng,0.0,1.0);
  double sum = 0.0;
  for (size_t i = 0; i < ps.size(); ++i)
  {
    sum += ps[i];
    if (u < sum) { return new VentureAtom(i); }
  }
  assert(false);
} 

double CategoricalSP::logDensityOutput(VentureValue * value, Node * node) const
{
  VentureAtom * i = dynamic_cast<VentureAtom *>(value);
  assert(i);
  VentureNumber * d = dynamic_cast<VentureNumber *>(node->operandNodes[i->n]->getValue());
  assert(d);

  return log(d->x);
}

vector<VentureValue*> CategoricalSP::enumerateOutput(Node * node) const
{
  VentureAtom * vold = dynamic_cast<VentureAtom*>(node->getValue());
  assert(vold);

  vector<VentureValue*> values;

  for (size_t i = 0; i < node->operandNodes.size(); ++i)
  {
    if (i == vold->n) { continue; }
    else {
      VentureNumber * d = dynamic_cast<VentureNumber *>(node->operandNodes[i]->getValue());
      assert(d);
      if (d->x > 0) { values.push_back(new VentureAtom(i)); }
    }
  }
  return values;
}

/* UniformDiscrete */
VentureValue * UniformDiscreteSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * a = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * b = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  assert(a);
  assert(b);
  int n = gsl_rng_uniform_int(rng, b->getInt() - a->getInt());
  return new VentureNumber(a->getInt() + n);
}

double UniformDiscreteSP::logDensityOutput(VentureValue * value, Node * node)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * a = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * b = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  VentureNumber * x = dynamic_cast<VentureNumber *>(value);
  assert(a);
  assert(b);
  assert(x);
  return log(gsl_ran_flat_pdf(x->getInt(),a->getInt(),b->getInt()));
}

vector<VentureValue*> UniformDiscreteSP::enumerateOutput(Node * node) const
{
  VentureNumber * vold = dynamic_cast<VentureNumber*>(node->getValue());
  assert(vold);

  vector<Node *> & operands = node->operandNodes;
  VentureNumber * a = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * b = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  assert(a);
  assert(b);
  
  vector<VentureValue*> values;

  for (int i = a->getInt(); i < b->getInt(); ++i)
  {
    if (i == vold->getInt()) { continue; }
    else { 
      values.push_back(new VentureNumber(i));
    }
  }
  return values;
}

/* Poisson */
VentureValue * PoissonSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * mu = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  assert(mu);
  return new VentureNumber(gsl_ran_poisson(rng,mu->x));
}

double PoissonSP::logDensityOutput(VentureValue * value, Node * node)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * mu = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * x = dynamic_cast<VentureNumber *>(value);
  assert(mu);
  assert(x);
  return log(gsl_ran_poisson_pdf(x->getInt(),mu->x));
}
