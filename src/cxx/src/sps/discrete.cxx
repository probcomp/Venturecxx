#include "node.h"
#include "sp.h"
#include "sps/discrete.h"
#include "value.h"

#include <vector>

VentureValue * FlipSP::simulateOutput(Node * node) 
{
  std::vector<Node *> operands = node->operandNodes;
  VentureDouble * p = dynamic_cast<VentureDouble *>(operands[0]->getValue());
  return new VentureDouble(d1->x + d2->x);
}

