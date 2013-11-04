#ifndef NODE_H
#define NODE_H

#include <vector>
#include <set>
#include <stdint.h>

using namespace std;

struct VentureValue;
struct VentureSP;
struct VentureEnvironment;
struct SPAux;

struct SP;
struct Trace;


enum class NodeType { VALUE, LOOKUP, REQUEST, OUTPUT };

struct Node
{
  static void addOperatorEdge(Node * operatorNode, Node * applicationNode);
  static void addOperandEdges(vector<Node *> operandNodes, Node * applicationNode);
  static void addRequestEdge(Node * requestNode, Node * outputNode);
  static void addESREdge(Node * node, Node * outputNode);
  static void addLookupEdge(Node * lookedUpNode, Node * lookupNode);

  /* 1D for 1 direction. We just clear outputNode->esrParents afterwards. */
  Node * removeLastESREdge();

  Node(NodeType type): nodeType(type) {}
  Node(NodeType type, VentureValue * value): nodeType(type), _value(value) {}
  Node(NodeType type, VentureValue * value, VentureEnvironment * familyEnv): 
    nodeType(type), _value(value), familyEnv(familyEnv) {}

  void disconnectLookup();
  void reconnectLookup();

  void registerReference(Node * lookedUpNode);
  bool isReference() const { return sourceNode != nullptr; }

  void registerObservation(VentureValue *val) { observedValue = val; }
  bool isObservation() const { return observedValue != nullptr; }

  void setValue(VentureValue *value);
  VentureValue * getValue() const;

  bool isApplication() { return nodeType == NodeType::REQUEST || nodeType == NodeType::OUTPUT; }

  /* Attributes */
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
  bool ownsValue{true};

  SPAux * madeSPAux{nullptr}; // owner

private:
  /* I like the constructor order, that's all. */
  VentureValue * _value{nullptr};

public:
  VentureEnvironment * familyEnv;


};



#endif
