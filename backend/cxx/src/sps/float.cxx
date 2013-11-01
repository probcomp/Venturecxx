#include "node.h"
#include "sp.h"
#include "sps/float.h"
#include "value.h"

#include <vector>

VentureValue * FloatPlusSP::simulateOutput(Node * node, gsl_rng * rng) 
{
  std::vector<Node *> operands = node->operandNodes;
  VentureDouble * d1 = dynamic_cast<VentureDouble *>(operands[0]->getValue());
  VentureDouble * d2 = dynamic_cast<VentureDouble *>(operands[1]->getValue());
  return new VentureDouble(d1->x + d2->x);
}

VentureValue * FloatTimesSP::simulateOutput(Node * node, gsl_rng * rng) 
{
  std::vector<Node *> operands = node->operandNodes;
  VentureDouble * d1 = dynamic_cast<VentureDouble *>(operands[0]->getValue());
  VentureDouble * d2 = dynamic_cast<VentureDouble *>(operands[1]->getValue());
  return new VentureDouble(d1->x * d2->x);
}

VentureValue * FloatDivideSP::simulateOutput(Node * node, gsl_rng * rng) 
{
    std::vector<Node *> operands = node->operandNodes;
    VentureDouble * d1 = dynamic_cast<VentureDouble *>(operands[0]->getValue());
    VentureDouble * d2 = dynamic_cast<VentureDouble *>(operands[1]->getValue());
    return new VentureDouble(d1->x / d2->x);
}

VentureValue * FloatEqualSP::simulateOutput(Node * node, gsl_rng * rng) 
{
  std::vector<Node *> operands = node->operandNodes;
  VentureDouble * d1 = dynamic_cast<VentureDouble *>(operands[0]->getValue());
  VentureDouble * d2 = dynamic_cast<VentureDouble *>(operands[1]->getValue());
  return new VentureBool(d1->x == d2->x);
}

VentureValue * FloatLessThanSP::simulateOutput(Node * node, gsl_rng * rng)
{
  std::vector<Node *> operands = node->operandNodes;
  VentureDouble * d1 = dynamic_cast<VentureDouble *>(operands[0]->getValue());
  VentureDouble * d2 = dynamic_cast<VentureDouble *>(operands[1]->getValue());
  return new VentureBool(d1->x < d2->x);
}

VentureValue * FloatGreaterThanSP::simulateOutput(Node * node, gsl_rng * rng) 
{
  std::vector<Node *> operands = node->operandNodes;
  VentureDouble * d1 = dynamic_cast<VentureDouble *>(operands[0]->getValue());
  VentureDouble * d2 = dynamic_cast<VentureDouble *>(operands[1]->getValue());
  return new VentureBool(d1->x > d2->x);
}

