#include <functional>
#include <tuple>

#include "render.h"
#include "trace.h"
#include "value.h"
#include "node.h"
#include "scaffold.h"

string quote(const string & str) { return "\"" + str + "\""; }
string nameOfNode(Node * node) { return to_string(reinterpret_cast<size_t>(node)); }

Renderer::Renderer() {}

void Renderer::reset()
{
  trace = nullptr;
  scaffold = nullptr;
  numClusters = 0;
  dot = "";
}

string Renderer::getNextClusterIndex()
{
  numClusters++;
  return to_string(numClusters);
}


void Renderer::dotTrace(Trace * trace, Scaffold * scaffold)
{
  reset();
  this->trace = trace;
  this->scaffold = scaffold;
  dotHeader();
//  dotStatements();
  dotNodes();
  dotEdges();
  dotFooter();
}

void Renderer::dotHeader()
{
  dot += "digraph {\nrankdir=BT\nfontsize=24\n";
}

void Renderer::dotFooter()
{
  dot += "\n}";
}

void Renderer::dotStatements()
{
  dot += "label=\""; 
  for (pair<size_t,pair<Node*,VentureValue*> > pp : trace->ventureFamilies)
  {
    dot += pp.second.second->toString() + "\\n";
  }
  dot += "\"\n";
}

void Renderer::dotNodes()
{
  dotVentureFamilies();
  dotSPFamilies();
}

void Renderer::dotSPFamilies()
{
  set<Node *> roots = trace->findSPFamilyRoots();
  for (Node * root : roots)
  {
    dotSubgraphStart("cluster" + getNextClusterIndex(),"");
    dotNodesInFamily(root);
    dotSubgraphEnd();
  }
}

void Renderer::dotVentureFamilies()
{
  dotSubgraphStart("cluster" + getNextClusterIndex(),"Venture Families");
  for (pair<size_t,pair<Node*,VentureValue*> > pp : trace->ventureFamilies)
  {
    // the expressions could live here
    dotSubgraphStart("cluster" + getNextClusterIndex(),to_string(pp.first));
    dotNodesInFamily(pp.second.first);
    dotSubgraphEnd();
  }
  dotSubgraphEnd();
}


void Renderer::dotSubgraphStart(string name,string label)
{
  dot += "subgraph " + name + " {\n";
  dot += "label="  + quote(label) + "\n";
}

void Renderer::dotSubgraphEnd()
{
  dot += "}\n\n";
}

void Renderer::dotNodesInFamily(Node * node)
{
  assert(node);
  if (node->nodeType == NodeType::VALUE) { dotNode(node); }
  else if (node->nodeType == NodeType::LOOKUP) { dotNode(node); }
  else
  {
    assert(node->nodeType == NodeType::OUTPUT);
    dotNode(node);
    dotNode(node->requestNode);
    dotNodesInFamily(node->operatorNode);
    for (Node * operandNode : node->operandNodes) { dotNodesInFamily(operandNode); }
  }
}


void Renderer::dotNode(Node * node) 
{
  // TODO may not work
  dot += quote(to_string(reinterpret_cast<size_t>(node)));
  dotAttributes(getNodeAttributes(node));
  dot += "\n";
}

map<string,string> Renderer::getNodeAttributes(Node * node) 
{
  return { 
    {"shape", getNodeShape(node)},
    {"fillcolor", getNodeFillColor(node)},
    {"style", getNodeStyle(node)},
    {"label", getNodeLabel(node)},
    {"fontsize", "24"}
  };
}


void Renderer::dotAttributes(const map<string,string> & attributes)
{    
  dot += "[";
  for (pair<string,string> p : attributes)
  {
    dot += quote(p.first) + "=" + quote(p.second) + " ";
  }
  dot += "]";
}

string Renderer::getNodeShape(Node * node) { return "ellipse"; }
string Renderer::getNodeFillColor(Node * node) 
{
  if (scaffold)
  {
    assert(false);
    return "black";
  }
  else
  {
    if (node->nodeType == NodeType::VALUE) { return "darkgoldenrod2"; }
    else if (node->nodeType == NodeType::LOOKUP) { return "khaki"; }
    else if (node->nodeType == NodeType::REQUEST) { return "darkolivegreen4"; }
    else
    {
      assert(node->nodeType == NodeType::OUTPUT);
      if (node->isObservation()) { return "magenta4"; }
      else if (node->isConstrained) { return "saddlebrown"; }
      else { return "dodgerblue"; }
    }
  }
}

string Renderer::getNodeStyle(Node * node) { return "filled"; }
string Renderer::getNodeLabel(Node * node) 
{
  // expression
  // value
  assert(node);
  string s = "";
  if (node->expression) { s += "exp: " + node->expression->toString() + "\\n"; }

  VentureValue * value = node->getValue();
  if (node->nodeType == NodeType::REQUEST) { s += "request: "; }
  else { s += "value: "; }

  if (value) 
  {
    VentureSP * vsp = dynamic_cast<VentureSP *>(value);
    if (vsp) { s += "sp:" + value->toString(); }
    else { s += value->toString(); }
  }
  else { s += "[]"; }
  return s;
}


// Edges
void Renderer::dotEdges() 
{
  set<Node *> roots = trace->findSPFamilyRoots();
  for (pair<size_t,pair<Node*,VentureValue*> > pp : trace->ventureFamilies)
  {
    roots.insert(pp.second.first); 
  }

  // now roots contains all roots
  for (Node * root : roots) { dotFamilyIncomingEdges(root); }

}

void Renderer::dotFamilyIncomingEdges(Node * node)
{
  assert(node);
  if (node->nodeType == NodeType::VALUE)
  {
    // do nothing
  }
  else if (node->nodeType == NodeType::LOOKUP) 
  { 
    dotEdge(Edge(node->lookedUpNode,node,EdgeType::LOOKUP));
  }
  else 
  {
    assert(node->nodeType == NodeType::OUTPUT);

    dotEdge(Edge(node->operatorNode,node,EdgeType::OP));
    dotEdge(Edge(node->operatorNode,node->requestNode,EdgeType::OP));
    dotFamilyIncomingEdges(node->operatorNode);

    for (Node * operandNode : node->operandNodes)
    {
      dotEdge(Edge(operandNode,node,EdgeType::ARG));
      dotEdge(Edge(operandNode,node->requestNode,EdgeType::ARG));
      dotFamilyIncomingEdges(operandNode);
    }

    dotEdge(Edge(node->requestNode,node,EdgeType::REQUEST));

    for (Node * esrParent : node->esrParents)
    {
      dotEdge(Edge(esrParent,node,EdgeType::ESR));
    }
  }
}

void Renderer::dotEdge(Edge e) 
{
  dot += quote(nameOfNode(e.start));
  dot += " -> ";
  dot += quote(nameOfNode(e.end));
  dotAttributes(getEdgeAttributes(e));
  dot += "\n";
}

map<string,string> Renderer::getEdgeAttributes(Edge e) 
{
  return { 
    {"arrowhead", getEdgeArrowhead(e)},
    {"style", getEdgeStyle(e)},
    {"color", getEdgeColor(e)},
  };
}


string Renderer::getEdgeArrowhead(Edge e) { return "normal"; }
string Renderer::getEdgeStyle(Edge e) { return "solid"; }
string Renderer::getEdgeColor(Edge e) { return "black"; }
