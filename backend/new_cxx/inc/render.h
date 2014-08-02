#ifndef RENDER_H
#define RENDER_H

#include <string>
#include <map>
#include <set>
#include "types.h"

struct ConcreteTrace;
struct Node;
struct Scaffold;

using namespace std;

enum EdgeType { OP,ARG,LOOKUP,ESR_PARENT,REQUEST_TO_OUTPUT,REQUEST };

struct Edge
{
Edge(Node * start, Node * end, enum EdgeType edgeType):
  start(start), end(end), edgeType(edgeType) {}

  Node * start;
  Node * end;
  enum EdgeType edgeType;
};

struct Renderer
{
  Renderer();
  void dotTrace(shared_ptr<ConcreteTrace> trace, shared_ptr<Scaffold> scaffold,bool labels,bool colorIgnored);

  void reset();
  string getNextClusterIndex();
  
  void dotHeader();
  void dotFooter();

  void dotStatements();
  void dotNodes();
  void dotEdges();
  void dotVentureFamilies();
  void dotSPFamilies();

  void dotNodesInFamily(Node * root);

  // Subgraphs
  void dotSubgraphStart(string name,string label);
  void dotSubgraphEnd();

  // Nodes
  void dotNode(Node * node);
  map<string,string> getNodeAttributes(Node * node);
  void dotAttributes(map<string,string> attributes);

  string getNodeShape(Node * node);
  string getNodeFillColor(Node * node);
  string getNodeStyle(Node * node);
  string getNodeLabel(Node * node);

  // Edges
  void dotFamilyIncomingEdges(Node * node);
  void dotEdge(Edge e);
  map<string,string> getEdgeAttributes(Edge e);
  string getEdgeArrowhead(Edge e);
  string getEdgeStyle(Edge e);
  string getEdgeColor(Edge e);
  string getEdgeConstraint(Edge e);

  set<Node *> nodes;

  shared_ptr<ConcreteTrace> trace;
  shared_ptr<Scaffold> scaffold;
  string dot;
  int numClusters;
  bool labels;
  bool colorIgnored;
  string clusterPrefix;

};

#endif
