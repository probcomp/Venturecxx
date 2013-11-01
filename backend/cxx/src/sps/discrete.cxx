#include "node.h"
#include "sp.h"
#include "sps/discrete.h"
#include "value.h"

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

#include <iostream>
#include <vector>

/* Bernoulli */

VentureValue * BernoulliSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  double p = dynamic_cast<VentureDouble *>(operands[0]->getValue())->x;
  assert(p >= 0 && p <= 1);
  uint32_t n = gsl_ran_bernoulli(rng,p);
  assert(n == 0 || n == 1);
  DPRINT("Bernoulli(", p);
  return new VentureBool(n);
} 

double BernoulliSP::logDensityOutput(VentureValue * value, Node * node) const
{

  vector<Node *> & operands = node->operandNodes;
  double p = dynamic_cast<VentureDouble *>(operands[0]->getValue())->x;
  assert(p >= 0 && p <= 1);
  bool b = dynamic_cast<VentureBool *>(value)->pred;

  if (b) { return log(p); }
  else { return log(1 - p); }
}

/* Categorical */
/* (categorical ps) */
VentureValue * CategoricalSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  VentureVector * vec = dynamic_cast<VentureVector *>(operands[0]->getValue());
  assert(vec);

  vector<VentureValue*> & xs = vec->xs;
  double u = gsl_ran_flat(rng,0.0,1.0);
  double sum = 0.0;
  for (size_t i = 0; i < xs.size(); ++i)
  {
    VentureDouble * d = dynamic_cast<VentureDouble *>(xs[i]);
    assert(d);
    double p = d->x;
    sum += p;
    if (u < sum) { return new VentureCount(i); }
  }
  assert(false);
  /* TODO normalize as a courtesy */
} 

double CategoricalSP::logDensityOutput(VentureValue * value, Node * node) const
{
  vector<Node *> & operands = node->operandNodes;
  VentureVector * vec = dynamic_cast<VentureVector *>(operands[0]->getValue());
  assert(vec);

  vector<VentureValue*> & xs = vec->xs;

  VentureCount * i = dynamic_cast<VentureCount *>(value);
  VentureDouble * p = dynamic_cast<VentureDouble *>(xs[i->n]);
  return log(p->x);
}
