// Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

#ifndef RENDER_H
#define RENDER_H

#include <boost/shared_ptr.hpp>
#include <string>
#include <map>
#include <set>
#include "types.h"

struct ConcreteTrace;
struct Node;
struct Scaffold;

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
  void dotTrace(boost::shared_ptr<ConcreteTrace> trace, boost::shared_ptr<Scaffold> scaffold,bool labels,bool colorIgnored);

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

  boost::shared_ptr<ConcreteTrace> trace;
  boost::shared_ptr<Scaffold> scaffold;
  string dot;
  int numClusters;
  bool labels;
  bool colorIgnored;
  string clusterPrefix;

};

#endif
