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

#include <boost/lexical_cast.hpp>
#include <boost/foreach.hpp>

#include "render.h"
#include "trace.h"
#include "concrete_trace.h"
#include "value.h"
#include "node.h"
#include "scaffold.h"

string quote(const string & str) { return "\"" + str + "\""; }
string to_string(int n) { return boost::lexical_cast<string>(n); }

string nameOfNode(Node * node) { return to_string(reinterpret_cast<size_t>(node)); }

Renderer::Renderer(): dot(""), numClusters(0), labels(true), colorIgnored(false), clusterPrefix("cluster") {}

void Renderer::reset()
{
  trace = boost::shared_ptr<ConcreteTrace>();
  scaffold = boost::shared_ptr<Scaffold>();
  numClusters = 0;
  dot = "";
}

string Renderer::getNextClusterIndex()
{
  numClusters++;
  return to_string(numClusters);
}


void Renderer::dotTrace(boost::shared_ptr<ConcreteTrace> trace, boost::shared_ptr<Scaffold> scaffold, bool labels, bool colorIgnored)
{
  reset();
  this->trace = trace;
  this->scaffold = scaffold;
  this->labels = labels;
  this->colorIgnored = colorIgnored;
  if (!labels) { clusterPrefix = "clster"; }
  else { clusterPrefix = "cluster"; }

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
  dot += "\"\n";
}

void Renderer::dotNodes()
{
  dotVentureFamilies();
  dotSPFamilies();
}

void Renderer::dotSPFamilies()
{
  for (map<Node*, boost::shared_ptr<VentureSPRecord> >::iterator iter1 = trace->madeSPRecords.begin();
       iter1 != trace->madeSPRecords.end();
       ++iter1)
    {
      boost::shared_ptr<SPFamilies> spFamilies = iter1->second->spFamilies;
      for (MapVVPtrRootOfFamily::iterator iter2  = spFamilies->families.begin();
	   iter2 != spFamilies->families.end();
	   ++iter2)
	{
	  dotSubgraphStart(clusterPrefix + getNextClusterIndex(),"");
	  dotNodesInFamily(iter2->second.get());
	  dotSubgraphEnd();
	}
    }
}

void Renderer::dotVentureFamilies()
{
  if (!labels) { assert(clusterPrefix != "cluster"); }
  dotSubgraphStart(clusterPrefix + getNextClusterIndex(),"Venture Families");
  for (map<DirectiveID,RootOfFamily>::iterator iter = trace->families.begin() ;
       iter != trace->families.end();
       ++iter)
    {
      // the expressions could live here
      dotSubgraphStart(clusterPrefix + getNextClusterIndex(),to_string(iter->first));
      dotNodesInFamily(iter->second.get());
      dotSubgraphEnd();
    }
  dotSubgraphEnd();
}


void Renderer::dotSubgraphStart(string name,string label)
{
  dot += "subgraph " + name + " {\n";
  if (labels) { dot += "label="  + quote(label) + "\n"; }
}

void Renderer::dotSubgraphEnd()
{
  dot += "}\n\n";
}

void Renderer::dotNodesInFamily(Node * node)
{
  assert(node);
  ConstantNode * constantNode = dynamic_cast<ConstantNode*>(node);
  LookupNode * lookupNode = dynamic_cast<LookupNode*>(node);
  OutputNode * outputNode = dynamic_cast<OutputNode*>(node);

  if (constantNode) { dotNode(node); }
  else if (lookupNode) { dotNode(node); }
  else
    {
      assert(outputNode);
      dotNode(outputNode);
      dotNode(outputNode->requestNode);
      dotNodesInFamily(outputNode->operatorNode);
      for (size_t i = 0; i < outputNode->operandNodes.size(); ++i)
	{
	  dotNodesInFamily(outputNode->operandNodes[i]); 
	}
    }
}


void Renderer::dotNode(Node * node) 
{
  nodes.insert(node);
  dot += quote(to_string(reinterpret_cast<size_t>(node)));
  dotAttributes(getNodeAttributes(node));
  dot += "\n";
}

map<string,string> Renderer::getNodeAttributes(Node * node) 
{
  map<string,string> m;
  m["shape"] = getNodeShape(node);
  m["fillcolor"] = getNodeFillColor(node);
  m["style"] = getNodeStyle(node);
  m["label"] = getNodeLabel(node);
  m["fontsize"] = "24";
  return m;
}


void Renderer::dotAttributes(map<string,string> attributes)
{    
  dot += "[";
  for (map<string,string>::iterator iter = attributes.begin();
       iter != attributes.end();
       ++iter)
    {
      dot += quote(iter->first) + "=" + quote(iter->second) + " ";
    }
  dot += "]";
}

string Renderer::getNodeShape(Node * node) {

  return "ellipse"; 
}

string Renderer::getNodeFillColor(Node * node) 
{
  if (scaffold)
    {
      if (scaffold->getPrincipalNodes().count(node)) { return "firebrick"; }
      else if (scaffold->isAAA(node)) { return "lightpink1"; }
      //    else if (scaffold->isResampling(node) && node->isObservation()) { return "magenta4"; }
      else if (scaffold->isResampling(node)) { return "gold"; }
      else if (scaffold->isAbsorbing(node)) { return "steelblue1"; }
      else if (scaffold->brush.count(node)) { return "darkseagreen"; }
      //      else if (colorIgnored && !scaffold->parents.count(node)) { return "grey90"; }
      else { return "grey60"; }
    }
  else
    {
      ConstantNode * constantNode = dynamic_cast<ConstantNode*>(node);
      LookupNode * lookupNode = dynamic_cast<LookupNode*>(node);
      RequestNode * requestNode = dynamic_cast<RequestNode*>(node);
      OutputNode * outputNode = dynamic_cast<OutputNode*>(node);

      if (constantNode) { return "darkgoldenrod2"; }
      else if (lookupNode) { return "khaki"; }
      else if (requestNode) { return "darkolivegreen4"; }
      else
	{
	  assert(outputNode);
	  if (trace->isObservation(outputNode)) { return "magenta4"; }
	  else if (trace->isConstrained(outputNode)) { return "saddlebrown"; }
	  else { return "dodgerblue"; }
	}
    }
}

string Renderer::getNodeStyle(Node * node) { return "filled"; }
string Renderer::getNodeLabel(Node * node) 
{
  if (!labels) 
    { 
      return "";
    }

  // expression
  // value
  assert(node);
  string s = "";
  if (!dynamic_pointer_cast<VentureNil>(node->exp)) { s += "exp: " + node->exp->asExpression() + "\\n"; }

  
  VentureValuePtr value = VentureValuePtr(new VentureNil());
  if (trace->values.count(node)) { value = trace->getValue(node); }
  
  if (dynamic_cast<RequestNode*>(node)) { s += "request: "; }
  else { s += "value: "; }

  if (value) { s += value->toString(); }
  else if (!(scaffold && scaffold->isResampling(node))) { s += "[]"; }

  return s;
}


// Edges
void Renderer::dotEdges() 
{
  for (map<Node*, boost::shared_ptr<VentureSPRecord> >::iterator iter1 = trace->madeSPRecords.begin();
       iter1 != trace->madeSPRecords.end();
       ++iter1)
    {
      boost::shared_ptr<SPFamilies> spFamilies = iter1->second->spFamilies;
      for (MapVVPtrRootOfFamily::iterator iter2  = spFamilies->families.begin();
	   iter2 != spFamilies->families.end();
	   ++iter2)
	{
	  dotFamilyIncomingEdges(iter2->second.get());
	}
    }

  for (map<DirectiveID,RootOfFamily>::iterator iter = trace->families.begin() ;
       iter != trace->families.end();
       ++iter)
    {
      dotFamilyIncomingEdges(iter->second.get());
    }
}

void Renderer::dotFamilyIncomingEdges(Node * node)
{
  assert(node);
  ConstantNode * constantNode = dynamic_cast<ConstantNode*>(node);
  LookupNode * lookupNode = dynamic_cast<LookupNode*>(node);
  OutputNode * outputNode = dynamic_cast<OutputNode*>(node);

  if (constantNode)
    {
      // do nothing
    }
  else if (lookupNode)
    { 
      dotEdge(Edge(lookupNode->sourceNode,node,LOOKUP));
    }
  else 
    {
      assert(outputNode);

      dotEdge(Edge(outputNode->operatorNode,node,OP));
      dotEdge(Edge(outputNode->operatorNode,outputNode->requestNode,OP));
      dotFamilyIncomingEdges(outputNode->operatorNode);

      for (size_t i = 0; i < outputNode->operandNodes.size(); ++i)
	{
	  Node * operandNode = outputNode->operandNodes[i];
	  dotEdge(Edge(operandNode,node,ARG));
	  dotEdge(Edge(operandNode,outputNode->requestNode,ARG));
	  dotFamilyIncomingEdges(operandNode);
	}

      dotEdge(Edge(outputNode->requestNode,outputNode,REQUEST_TO_OUTPUT));

      vector<RootOfFamily> esrRoots = trace->getESRParents(node);
      for (size_t i = 0; i < esrRoots.size(); ++i) 
	{ 
	  dotEdge(Edge(esrRoots[i].get(),node,ESR_PARENT));
	  dotEdge(Edge(outputNode->requestNode,esrRoots[i].get(),REQUEST));
	}
    }
}

void Renderer::dotEdge(Edge e) 
{
  if (!labels && (!nodes.count(e.start) || !nodes.count(e.end))) { return; }
  dot += quote(nameOfNode(e.start));
  dot += " -> ";
  dot += quote(nameOfNode(e.end));
  dotAttributes(getEdgeAttributes(e));
  dot += "\n";
}

map<string,string> Renderer::getEdgeAttributes(Edge e) 
{
  map<string,string> m;
  m["arrowhead"] = getEdgeArrowhead(e);
  m["style"] = getEdgeStyle(e);
  m["color"] = getEdgeColor(e);
  m["constraint"] = getEdgeConstraint(e);
  return m;
}


string Renderer::getEdgeArrowhead(Edge e) { return "normal"; }
string Renderer::getEdgeStyle(Edge e) 
{ 
  if (e.edgeType == REQUEST) { return "dotted"; }
  return "solid"; 
}
string Renderer::getEdgeColor(Edge e) { return "black"; }
string Renderer::getEdgeConstraint(Edge e) 
{   
  if (e.edgeType == REQUEST) { return "false"; }
  return "true"; 
}
