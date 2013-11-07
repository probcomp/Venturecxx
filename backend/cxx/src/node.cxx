#include "node.h"
#include "value.h"
#include <cassert>

string strNodeType(NodeType nt)
{
  switch (nt)
  {
  case NodeType::VALUE: return "value";
  case NodeType::LOOKUP: return "lookup";
  case NodeType::REQUEST: return "request";
  case NodeType::OUTPUT: return "output";
  default: { return "<none>"; }
  }
}

/* Static member functions */

void Node::addOperatorEdge(Node * operatorNode, Node * applicationNode)
{
  operatorNode->children.insert(applicationNode);

  applicationNode->operatorNode = operatorNode;
}

void Node::addOperandEdges(vector<Node *> operandNodes, Node * applicationNode)
{
  for (Node * operandNode : operandNodes)
    {
      operandNode->children.insert(applicationNode);
    }
  applicationNode->operandNodes = operandNodes;
}

void Node::addRequestEdge(Node * requestNode, Node * outputNode)
{
  requestNode->children.insert(outputNode);

  outputNode->requestNode = requestNode;

  /* Not necessary, but convenient. */
  requestNode->outputNode = outputNode; 
}

void Node::addESREdge(Node * esrNode, Node * outputNode)
{  
//  cout << "ADD " << esrNode << outputNode << endl;
  esrNode->children.insert(outputNode);

  outputNode->esrParents.push_back(esrNode);
  esrNode->numRequests++;
}

Node * Node::removeLastESREdge()
{
//  cout << "REMOVE " << this << endl;
  assert(!esrParents.empty());
  Node * esrParent = esrParents.back();
  assert(esrParent);
  esrParent->children.erase(this);
  esrParent->numRequests--;
  esrParents.pop_back();
  return esrParent;
}
 
void Node::addLookupEdge(Node * lookedUpNode, Node * lookupNode)
{

  lookedUpNode->children.insert(lookupNode);
  lookupNode->lookedUpNode = lookedUpNode;
}

/* We only disconnect a node from the trace if it has no
   children, and we only do so when its entire family is
   being destroyed. All ESRParents will be detached during
   unapplyPSP, so the only other non-family parents will
   be lookups. */
void Node::disconnectLookup()
{
  this->lookedUpNode->children.erase(this);
}

void Node::reconnectLookup()
{
  this->lookedUpNode->children.insert(this);
}

/* This is called after the appropriate "edges" are added. */
void Node::registerReference(Node * lookedUpNode)
{
  assert(_value == nullptr);
  if (lookedUpNode->isReference())
    {
      this->sourceNode = lookedUpNode->sourceNode;
    }
  else
    {
      this->sourceNode = lookedUpNode;
    }
}

void Node::setValue(VentureValue *value)
{
  assert(!isReference());
  assert(value);
  
  _value = value;
}

/* If a node is a reference, we return the value of its
   source node. Otherwise we just return this node's value. */
VentureValue * Node::getValue() const
{
  if (this->isReference())
  {
    assert(this->sourceNode);
    assert(!this->sourceNode->isReference());
    return this->sourceNode->getValue();
  }
  else
  {
    if (!_value) { WPRINT("node.getValue(): ", _value); }
    return _value;
  }
}


VentureSP * Node::vsp()
{
  VentureSP * _vsp = dynamic_cast<VentureSP*>(operatorNode->getValue());
  assert(_vsp);
  return _vsp;
}

SP * Node::sp() { return vsp()->sp; }
SPAux * Node::spaux() { return vsp()->makerNode->madeSPAux; }

bool Node::isValid() 
{ 
  return (magic == 65314235) &&
    (nodeType == NodeType::VALUE || 
     nodeType == NodeType::LOOKUP ||
     nodeType == NodeType::REQUEST ||
     nodeType == NodeType::OUTPUT);
}
