#include "node.h"
#include "value.h"


#include "sp.h"
#include "sps/vector.h"

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

#include <cassert>
#include <iostream>
#include <typeinfo>

VentureValue * MakeVectorSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<VentureValue *> vec;
  for (Node * operand : node->operandNodes)
  {
    vec.push_back(operand->getValue());
  }
  return new VentureVector(vec);
}

VentureValue * VectorLookupSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  VentureVector * vec = dynamic_cast<VentureVector *>(operands[0]->getValue());
  VentureAtom * i = dynamic_cast<VentureAtom *>(operands[1]->getValue());
  assert(vec);
  assert(i);

  return vec->xs[i->n];
}
