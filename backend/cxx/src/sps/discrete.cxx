#include "node.h"
#include "sp.h"
#include "sps/discrete.h"
#include "value.h"
#include "utils.h"

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

#include <iostream>
#include <vector>

/* Bernoulli */

VentureValue * BernoulliSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * p = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  assert(p);
  assert(p->x >= 0 && p->x <= 1);
  uint32_t n = gsl_ran_bernoulli(rng,p->x);
  assert(n == 0 || n == 1);
  DPRINT("Bernoulli(", p->x);
  return new VentureBool(n);
} 

double BernoulliSP::logDensityOutput(VentureValue * value, Node * node) const
{

  vector<Node *> & operands = node->operandNodes;
  VentureNumber * p = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  assert(p);
  assert(p->x >= 0 && p->x <= 1);
  VentureBool * b = dynamic_cast<VentureBool *>(value);
  assert(b);

  if (b->pred) { return log(p->x); }
  else { return log(1 - p->x); }
}

vector<VentureValue*> BernoulliSP::enumerateOutput(Node * node) const
{
  VentureBool * vold = dynamic_cast<VentureBool*>(node->getValue());
  assert(vold);
  if (vold->pred) { return {new VentureBool(false)}; }
  else { return {new VentureBool(true)}; }
}

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
  VentureNumber * p = dynamic_cast<VentureNumber *>(node->operandNodes[i->n]->getValue());
  assert(p);
  return log(p->x);
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
      values.push_back(new VentureAtom(i));
    }
  }
  return values;
}
