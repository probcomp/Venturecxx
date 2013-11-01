#include "address.h"
#include "node.h"
#include "trace.h"
#include "primitives.h"
#include "sp.h"


#include <iostream>
#include <cassert>

Trace::Trace()
{
  addPrimitives();
  addEnvironments();
}

void Trace::addPrimitives()
{
  /* Add built-in values. */
  for (std::pair<std::string,VentureValue *> p : builtInValues) 
    { 
      Node * node = makeNode(Address(p.first),NodeType::VALUE);
      node->setValue(p.second);
    }

  /* Add built-in SPs. */
  for (std::pair<std::string,VentureSPValue *> p : builtInSPs) 
    { 
      Node * node = makeNode(Address(p.first),NodeType::VALUE);
      node->setValue(p.second);
    }
}

void Trace::addEnvironments()
{
  /* Create empty environment. */
  Environment emptyEnv(Address::nullAddress.toString());
  Node * emptyEnvNode = makeNode(Address::emptyEnvironmentAddress,NodeType::VALUE);
  emptyEnvNode->setValue(new VentureEnvironment(emptyEnv));
  
  /* Create primitives environment. */
  Environment primitivesEnv(emptyEnvNode->address);
  for (std::pair<std::string,VentureValue *> p : builtInValues) 
    { 
      primitivesEnv.addBinding(p.first,Address(p.first)); 
    }

  for (std::pair<std::string,VentureSPValue *> p : builtInSPs) 
    { 
      Address address = p.second->sp->address;
      primitivesEnv.addBinding(address.toString(),address); 
    }

  Node * primitivesEnvNode = makeNode(Address::primitivesEnvironmentAddress,NodeType::VALUE);
  primitivesEnvNode->setValue(new VentureEnvironment(primitivesEnv));

  /* Create global environment. */
  Environment globalEnv(primitivesEnvNode->address);
  Node * globalEnvNode = makeNode(Address::globalEnvironmentAddress,NodeType::VALUE);
  globalEnvNode->setValue(new VentureEnvironment(globalEnv));
  
}

VentureValue * Trace::getValue(Address addr)
{
  return _map[addr]->getValue();
}


Node * Trace::makeNode(const Address & address, NodeType nodeType)
{
  assert(_map.count(address) == 0);
  Node * node = new Node(address,nodeType);
  _map.insert({address, node});
  return node;
}

void Trace::destroyNode(Node * node)
{
  assert(_map.count(node->address) == 1);
  _map.erase(node->address);
  /* TODO confirm syntax. */
  delete node;
}


void Trace::addApplicationEdges(Node * requestNode, Node * outputNode, uint8_t numOperands)
{
  /* Operator edges. */
  Node * operatorNode = getNode(outputNode->address.getOperatorAddress());
  Node::addOperatorEdge(operatorNode,requestNode);
  Node::addOperatorEdge(operatorNode,outputNode);

  /* Operand edges. */
  std::vector<Node *> operandNodes;
  for (uint8_t i = 0; i < numOperands; ++i)
    {
      /* Be careful about the indexing. Will want to fix this. */
      operandNodes.push_back(getNode(outputNode->address.getOperandAddress(i+1)));
    }
  Node::addOperandEdges(operandNodes, requestNode);
  Node::addOperandEdges(operandNodes, outputNode);

  /* Request edge. */
  Node::addRequestEdge(requestNode, outputNode);
}

Environment * Trace::getGlobalEnvironment() const
{
  Node * globalEnvNode = getNode(Address::globalEnvironmentAddress);
  VentureEnvironment * ventureEnv = dynamic_cast<VentureEnvironment *>(globalEnvNode->getValue());
  /* TODO not worth it, just make environments pointers again. */
  return &ventureEnv->env;
}


Node * Trace::findSymbol(std::string symbol, Address environmentAddress) 
{
  Node * envNode = _map[environmentAddress];
  VentureEnvironment * venv = dynamic_cast<VentureEnvironment *>(envNode->getValue());
  if (venv->env.frame.count(symbol) == 1)
    {
      return _map[venv->env.frame[symbol]];
    }
  else
    {
      return findSymbol(symbol,venv->env.outerEnvAddr);
    }
}

/* CURRENT
void Trace::vladEvalExpression(std::string addressName, boost::python::object object)
{
  Exp exp = parseExpressionFromBPObject(object);
  ...

}
*/
