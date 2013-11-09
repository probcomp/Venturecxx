#include "node.h"
#include "sp.h"
#include "sps/number.h"
#include "value.h"
#include <cassert>
#include <vector>
#include <math.h>

VentureValue * PlusSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  double sum = 0;
  for (size_t i = 0; i < operands.size(); ++i)
  {
    VentureNumber * vdouble = dynamic_cast<VentureNumber *>(operands[i]->getValue());
    assert(vdouble);
    sum += vdouble->x;
  }
  return new VentureNumber(sum);
}


VentureValue * MinusSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * d1 = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * d2 = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  assert(d1);
  assert(d2);
  return new VentureNumber(d1->x - d2->x);
}

VentureValue * TimesSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  double prod = 1;
  for (size_t i = 0; i < operands.size(); ++i)
  {
    VentureNumber * vdouble = dynamic_cast<VentureNumber *>(operands[i]->getValue());
    assert(vdouble);
    prod *= vdouble->x;
  }
  return new VentureNumber(prod);
}

VentureValue * DivideSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
    vector<Node *> & operands = node->operandNodes;
    VentureNumber * d1 = dynamic_cast<VentureNumber *>(operands[0]->getValue());
    VentureNumber * d2 = dynamic_cast<VentureNumber *>(operands[1]->getValue());
    assert(d1);
    assert(d2);
    return new VentureNumber(d1->x / d2->x);
}

VentureValue * PowerSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
    vector<Node *> & operands = node->operandNodes;
    VentureNumber * d1 = dynamic_cast<VentureNumber *>(operands[0]->getValue());
    VentureNumber * d2 = dynamic_cast<VentureNumber *>(operands[1]->getValue());
    assert(d1);
    assert(d2);
    return new VentureNumber(pow(d1->x, d2->x));
}

VentureValue * EqualSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * d1 = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * d2 = dynamic_cast<VentureNumber *>(operands[1]->getValue());

  if (d1 && d2) { return new VentureBool(d1->x == d2->x); }

  VentureBool * b1 = dynamic_cast<VentureBool *>(operands[0]->getValue());
  VentureBool * b2 = dynamic_cast<VentureBool *>(operands[1]->getValue());

  if (b1 && b2) { return new VentureBool(b1->pred == b2->pred); }

  VentureAtom * a1 = dynamic_cast<VentureAtom *>(operands[0]->getValue());
  VentureAtom * a2 = dynamic_cast<VentureAtom *>(operands[1]->getValue());

  if (a1 && a2) { return new VentureBool(a1->n == a2->n); }

  VentureSymbol * s1 = dynamic_cast<VentureSymbol *>(operands[0]->getValue());
  VentureSymbol * s2 = dynamic_cast<VentureSymbol *>(operands[1]->getValue());

  if (s1 && s2) { return new VentureBool(s1->sym == s2->sym); }

  return new VentureBool(false);
}

VentureValue * LessThanSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * d1 = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * d2 = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  assert(d1);
  assert(d2);
  return new VentureBool(d1->x < d2->x);
}

VentureValue * GreaterThanSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * d1 = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * d2 = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  assert(d1);
  assert(d2);
  return new VentureBool(d1->x > d2->x);
}

VentureValue * LessThanOrEqualToSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * d1 = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * d2 = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  assert(d1);
  assert(d2);
  return new VentureBool(d1->x <= d2->x);
}

VentureValue * GreaterThanOrEqualToSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * d1 = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * d2 = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  assert(d1);
  assert(d2);
  return new VentureBool(d1->x >= d2->x);
}

VentureValue * RealSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureAtom * a = dynamic_cast<VentureAtom *>(operands[0]->getValue());
  assert(a);
  return new VentureNumber(a->n);
}

VentureValue * AtomEqualSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureAtom * d1 = dynamic_cast<VentureAtom *>(operands[0]->getValue());
  VentureAtom * d2 = dynamic_cast<VentureAtom *>(operands[1]->getValue());
  assert(d1);
  assert(d2);
  return new VentureBool(d1->n == d2->n);
}
