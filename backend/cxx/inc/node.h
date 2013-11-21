#ifndef NODE_H
#define NODE_H

#include "all.h"
#include "address.h"
#include <string>
#include <vector>
#include <set>
#include <stdint.h>
#include <cassert>


struct VentureValue;
struct VentureSP;
struct VentureEnvironment;
struct SPAux;

struct SP;
struct Trace;


enum class NodeType { VALUE, LOOKUP, REQUEST, OUTPUT };
string strNodeType(NodeType nt);


struct Node
{
  static void addOperatorEdge(Node * operatorNode, Node * applicationNode);
  static void addOperandEdges(vector<Node *> operandNodes, Node * applicationNode);
  static void addRequestEdge(Node * requestNode, Node * outputNode);
  static void addESREdge(Node * node, Node * outputNode);
  static void addLookupEdge(Node * lookedUpNode, Node * lookupNode);

  /* 1D for 1 direction. We just clear outputNode->esrParents afterwards. */
  Node * removeLastESREdge();

  Node(Address addr, NodeType type): address(addr), nodeType(type) {}
  Node(Address addr, NodeType type, VentureValue * value): address(addr), nodeType(type), _value(value) {}
  Node(Address addr, NodeType type, VentureValue * value, VentureEnvironment * familyEnv): 
    address(addr), nodeType(type), _value(value), familyEnv(familyEnv) {}



  void disconnectLookup();
  void reconnectLookup();

  void registerReference(Node * lookedUpNode);
  bool isReference() const { return sourceNode != nullptr; }

  void registerObservation(VentureValue *val) { observedValue = val; }
  bool isObservation() const { return observedValue != nullptr; }

  void setValue(VentureValue *value);
  void clearValue();
  VentureValue * getValue() const;

  bool isApplication() { return nodeType == NodeType::REQUEST || nodeType == NodeType::OUTPUT; }



  /* Attributes */
  const Address address;
  const NodeType nodeType;

  Node * lookedUpNode{nullptr};
  Node * sourceNode{nullptr};

  bool isActive{false};

  set<Node*> children{};
  uint32_t numRequests{0};

  VentureValue * observedValue{nullptr};
  Node * operatorNode{nullptr};
  vector<Node *> operandNodes{};

  VentureSP * vsp();
  SP * sp();
  SPAux * spaux();

  vector<Node *> esrParents{};
  Node * requestNode{nullptr};
  Node * outputNode{nullptr};
  bool isConstrained{false};
  bool spOwnsValue{true};

  SPAux * madeSPAux{nullptr}; // owner

  bool isValid() { return magic == 653135; }
  uint32_t magic = 653135;
  ~Node() { assert(isValid()); magic = 0; }

  /* I like the constructor order, that's all. */
  VentureValue * _value{nullptr};


  VentureEnvironment * familyEnv;


};



#endif
