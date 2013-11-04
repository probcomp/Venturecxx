#include "node.h"
#include "sp.h"
#include "sps/real.h"
#include "value.h"
#include <cassert>
#include <vector>

VentureValue * RealPlusSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  double sum = 0;
  for (size_t i = 0; i < operands.size(); ++i)
  {
    VentureDouble * vdouble = dynamic_cast<VentureDouble *>(operands[i]->getValue());
    assert(vdouble);
    sum += vdouble->x;
  }
  return new VentureDouble(sum);
}


VentureValue * RealMinusSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureDouble * d1 = dynamic_cast<VentureDouble *>(operands[0]->getValue());
  VentureDouble * d2 = dynamic_cast<VentureDouble *>(operands[1]->getValue());
  assert(d1);
  assert(d2);
  return new VentureDouble(d1->x - d2->x);
}

VentureValue * RealTimesSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  double prod = 1;
  for (size_t i = 0; i < operands.size(); ++i)
  {
    VentureDouble * vdouble = dynamic_cast<VentureDouble *>(operands[i]->getValue());
    assert(vdouble);
    prod *= vdouble->x;
  }
  return new VentureDouble(prod);
}

VentureValue * RealDivideSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
    vector<Node *> & operands = node->operandNodes;
    VentureDouble * d1 = dynamic_cast<VentureDouble *>(operands[0]->getValue());
    VentureDouble * d2 = dynamic_cast<VentureDouble *>(operands[1]->getValue());
    assert(d1);
    assert(d2);
    return new VentureDouble(d1->x / d2->x);
}

VentureValue * RealEqualSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureDouble * d1 = dynamic_cast<VentureDouble *>(operands[0]->getValue());
  VentureDouble * d2 = dynamic_cast<VentureDouble *>(operands[1]->getValue());
  assert(d1);
  assert(d2);
  return new VentureBool(d1->x == d2->x);
}

VentureValue * RealLessThanSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  VentureDouble * d1 = dynamic_cast<VentureDouble *>(operands[0]->getValue());
  VentureDouble * d2 = dynamic_cast<VentureDouble *>(operands[1]->getValue());
  assert(d1);
  assert(d2);
  return new VentureBool(d1->x < d2->x);
}

VentureValue * RealGreaterThanSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureDouble * d1 = dynamic_cast<VentureDouble *>(operands[0]->getValue());
  VentureDouble * d2 = dynamic_cast<VentureDouble *>(operands[1]->getValue());
  assert(d1);
  assert(d2);
  return new VentureBool(d1->x > d2->x);
}

