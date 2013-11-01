#ifndef NODE_H
#define NODE_H

#include <vector>
#include <set>
#include <cassert>
#include <stdint.h>

#include "value.h"
#include "value_types.h"
#include "address.h"
#include "sp.h"


#include <iostream>

enum class NodeType { FAMILY_ENV, VALUE, LOOKUP, REQUEST, OUTPUT };

inline std::string nodeTypeToString(NodeType nodeType)
{
  switch (nodeType)
    {
    case NodeType::VALUE: return "value";
    case NodeType::LOOKUP: return "lookup";
    case NodeType::FAMILY_ENV: return "familyEnv";
    case NodeType::REQUEST: return "request";
    case NodeType::OUTPUT: return "output";
    }
  return "<error>";
}

struct Node
{
  static void addOperatorEdge(Node * operatorNode, Node * applicationNode);
  static void addOperandEdges(std::vector<Node *> operandNodes, Node * applicationNode);
  static void addRequestEdge(Node * requestNode, Node * outputNode);
  static void addCSREdge(Node * node, Node * outputNode);
  static void addLookupEdge(Node * lookedUpNode, Node * lookupNode);

  /* 1D for 1 direction. We just clear outputNode->csrParents afterwards. */
  static void removeCSREdge1D(Node * csrNode,Node * outputNode);

  Node(const Address & addr, NodeType type): address(addr), nodeType(type) {}

  VentureValue * getValue() const;
  void disconnectLookup();


  void registerReference(Node * lookedUpNode);
  bool isReference() const { return sourceNode != nullptr; }

  void registerObservation(VentureValue *val) { observedValue = val; }
  bool isObservation() const { return observedValue != nullptr; }

  void setValue(VentureValue *value);

  bool isApplication() { return nodeType == NodeType::REQUEST || nodeType == NodeType::OUTPUT; }

  /* Attributes */
  const Address address{};
  const NodeType nodeType{NodeType::VALUE};
  bool isActive{false};
  Node * sourceNode{nullptr};
  Node * lookedUpNode{nullptr};
  Address familyEnvAddr{};

  std::set<Node*> children{};
  uint32_t numRequests{0};

  VentureValue * observedValue{nullptr};
  Node * operatorNode{nullptr};
  std::vector<Node *> operandNodes{};

  VentureSPValue * ventureSPValue{nullptr};
  SP * sp{nullptr};
  SPAux * spAux{nullptr};

  std::vector<Node *> csrParents{};
  Node * requestNode{nullptr};
  Node * outputNode{nullptr};
  bool isConstrained{false};

  /* Redundant, but computed as a way of caching.*/
  std::vector<Node *> parents{};
  bool isParentOfApp{false};

private:
  VentureValue * _value{nullptr};

};



#endif
