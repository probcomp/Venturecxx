#include "trace.h"
#include <iostream>

void Trace::registerRandomChoice(Node * node)
{
  assert(!rcToIndex.count(node));

  rcToIndex[node] = randomChoices.size();
  randomChoices.push_back(node);
}


void Trace::unregisterRandomChoice(Node * node)
{
  assert(rcToIndex.count(node));

  uint32_t index = rcToIndex[node];
  uint32_t lastIndex = randomChoices.size()-1;

  Node * lastNode = randomChoices[lastIndex];
  rcToIndex[lastNode] = index;
  randomChoices[index] = lastNode;
  randomChoices.pop_back();
  rcToIndex.erase(node);
  assert(rcToIndex.size() == randomChoices.size());
}

void Trace::registerAEKernel(Node * node)
{
  std::cout << "Warning -- Trace::registerAEKernel not yet implemented." << std::endl;
}

void Trace::unregisterAEKernel(Node * node)
{
  std::cout << "Warning -- Trace::unregisterAEKernel yet implemented." << std::endl;
}

