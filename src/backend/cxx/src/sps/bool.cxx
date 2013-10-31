#include "node.h"
#include "sp.h"
#include "sps/bool.h"
#include "value.h"

#include <vector>

VentureValue * BoolAndSP::simulateOutput(Node * node, gsl_rng * rng) 
{
  std::vector<Node *> operands = node->operandNodes;
  VentureBool * b1 = dynamic_cast<VentureBool *>(operands[0]->getValue());
  VentureBool * b2 = dynamic_cast<VentureBool *>(operands[1]->getValue());
  return new VentureBool(b1->pred && b2->pred);
}

VentureValue * BoolOrSP::simulateOutput(Node * node, gsl_rng * rng) 
{
  std::vector<Node *> operands = node->operandNodes;
  VentureBool * b1 = dynamic_cast<VentureBool *>(operands[0]->getValue());
  VentureBool * b2 = dynamic_cast<VentureBool *>(operands[1]->getValue());
  return new VentureBool(b1->pred || b2->pred);
}

VentureValue * BoolNotSP::simulateOutput(Node * node, gsl_rng * rng) 
{
    std::vector<Node *> operands = node->operandNodes;
    VentureBool * b = dynamic_cast<VentureBool *>(operands[0]->getValue());
    return new VentureBool(!b->pred);
}

VentureValue * BoolXorSP::simulateOutput(Node * node, gsl_rng * rng) 
{
  std::vector<Node *> operands = node->operandNodes;
  VentureBool * b1 = dynamic_cast<VentureBool *>(operands[0]->getValue());
  VentureBool * b2 = dynamic_cast<VentureBool *>(operands[1]->getValue());
  return new VentureBool((b1->pred && !b2->pred) || (b2->pred && !b1->pred));
}

