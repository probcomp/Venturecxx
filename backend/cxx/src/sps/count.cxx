#include "node.h"
#include "sp.h"
#include "sps/count.h"
#include "value.h"
#include <cassert>
#include <vector>

VentureValue * CountPlusSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureCount * d1 = dynamic_cast<VentureCount *>(operands[0]->getValue());
  VentureCount * d2 = dynamic_cast<VentureCount *>(operands[1]->getValue());
  assert(d1);
  assert(d2);
  return new VentureCount(d1->n + d2->n);
}

VentureValue * CountTimesSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureCount * d1 = dynamic_cast<VentureCount *>(operands[0]->getValue());
  VentureCount * d2 = dynamic_cast<VentureCount *>(operands[1]->getValue());
  assert(d1);
  assert(d2);
  return new VentureCount(d1->n * d2->n);
}

VentureValue * CountDivideSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
    vector<Node *> & operands = node->operandNodes;
    VentureCount * d1 = dynamic_cast<VentureCount *>(operands[0]->getValue());
    VentureCount * d2 = dynamic_cast<VentureCount *>(operands[1]->getValue());
    assert(d1);
    assert(d2);
    return new VentureCount(d1->n / d2->n);
}

VentureValue * CountEqualSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureCount * d1 = dynamic_cast<VentureCount *>(operands[0]->getValue());
  VentureCount * d2 = dynamic_cast<VentureCount *>(operands[1]->getValue());
  assert(d1);
  assert(d2);
  return new VentureBool(d1->n == d2->n);
}

VentureValue * CountLessThanSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  VentureCount * d1 = dynamic_cast<VentureCount *>(operands[0]->getValue());
  VentureCount * d2 = dynamic_cast<VentureCount *>(operands[1]->getValue());
  assert(d1);
  assert(d2);
  return new VentureBool(d1->n < d2->n);
}

VentureValue * CountGreaterThanSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureCount * d1 = dynamic_cast<VentureCount *>(operands[0]->getValue());
  VentureCount * d2 = dynamic_cast<VentureCount *>(operands[1]->getValue());
  assert(d1);
  assert(d2);
  return new VentureBool(d1->n > d2->n);
}

