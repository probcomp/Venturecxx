#include "sp.h"
#include "node.h"

/* All of these methods simply check the node type, and dispatch
   to REQUEST or OUTPUT as appropriate. */

VentureValue * SP::simulate(Node * node, gsl_rng * rng)
{
  if (node->nodeType == NodeType::REQUEST)
  { return this->simulateRequest(node,rng); }
  else 
  { 
    assert(node->nodeType == NodeType::OUTPUT);
    return this->simulateOutput(node,rng); 
  }
}

double SP::logDensity(VentureValue * value, Node * node)
{
  if (node->nodeType == NodeType::REQUEST)
  { return this->logDensityRequest(value,node); }
  else 
  { 
    assert(node->nodeType == NodeType::OUTPUT);
    return this->logDensityOutput(value,node); 
  }
}

void SP::incorporate(VentureValue * value, Node * node)
{
  if (node->nodeType == NodeType::REQUEST)
  { return this->incorporateRequest(value,node); }
  else 
  { 
    assert(node->nodeType == NodeType::OUTPUT);
    return this->incorporateOutput(value,node); 
  }
}


void SP::remove(VentureValue * value, Node * node)
{
  if (node->nodeType == NodeType::REQUEST)
  { return this->removeRequest(value,node); }
  else 
  { 
    assert(node->nodeType == NodeType::OUTPUT);
    return this->removeOutput(value,node); 
  }
}

bool SP::canAbsorb(NodeType nodeType)
{
  if (nodeType == NodeType::REQUEST)
  { return canAbsorbRequest; }
  else 
  { 
    assert(nodeType == NodeType::OUTPUT);
    return canAbsorbOutput; 
  }
}

bool SP::isRandom(NodeType nodeType)
{
  if (nodeType == NodeType::REQUEST)
  { return isRandomRequest; }
  else 
  { 
    assert(nodeType == NodeType::OUTPUT);
    return isRandomOutput; 
  }
}


