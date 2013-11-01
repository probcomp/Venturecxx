#include "node.h"
#include <string>

/* Static member functions */

void Node::addOperatorEdge(Node * operatorNode, Node * applicationNode)
{
  operatorNode->children.insert(applicationNode);

  operatorNode->isParentOfApp = true;

  applicationNode->operatorNode = operatorNode;
  applicationNode->ventureSPValue = dynamic_cast<VentureSPValue *>(operatorNode->getValue());
  applicationNode->sp = applicationNode->ventureSPValue->sp;
  applicationNode->spAux = applicationNode->ventureSPValue->spAux;
}

void Node::addOperandEdges(std::vector<Node *> operandNodes, Node * applicationNode)
{
  for (Node * operandNode : operandNodes)
    {
      operandNode->children.insert(applicationNode);

      operandNode->isParentOfApp = true;
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

void Node::addCSREdge(Node * csrNode, Node * outputNode)
{  
  csrNode->children.insert(outputNode);

  outputNode->csrParents.push_back(csrNode);
  csrNode->numRequests++;
}

void Node::removeCSREdge1D(Node * csrNode,Node * outputNode)
{
  csrNode->children.erase(outputNode);
  csrNode->numRequests--;
}

 
void Node::addLookupEdge(Node * lookedUpNode, Node * lookupNode)
{

  lookedUpNode->children.insert(lookupNode);
  lookupNode->lookedUpNode = lookedUpNode;
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
      return this->_value;
    }
}

/* We only disconnect a node from the trace if it has no
   children, and we only do so when its entire family is
   being destroyed. All CSRParents will be detached during
   unapplyPSP, so the only other non-family parents will
   be lookups. */
void Node::disconnectLookup()
{
  this->lookedUpNode->children.erase(this);
}

/* This is called after the appropriate "edges" are added. */
void Node::registerReference(Node * lookedUpNode)
{
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
  assert(!this->isReference());
  this->_value = value;
}

