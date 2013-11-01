#include "node.h"
#include "sp.h"
#include "sps/real.h"
#include "value.h"
#include <cassert>
#include <vector>

VentureValue * RealPlusSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureDouble * d1 = dynamic_cast<VentureDouble *>(operands[0]->getValue());
  VentureDouble * d2 = dynamic_cast<VentureDouble *>(operands[1]->getValue());
  assert(d1);
  assert(d2);
  return new VentureDouble(d1->x + d2->x);
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
  VentureDouble * d1 = dynamic_cast<VentureDouble *>(operands[0]->getValue());
  VentureDouble * d2 = dynamic_cast<VentureDouble *>(operands[1]->getValue());
  assert(d1);
  assert(d2);
  return new VentureDouble(d1->x * d2->x);
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

