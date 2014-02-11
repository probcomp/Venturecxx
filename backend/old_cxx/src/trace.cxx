/*
* Copyright (c) 2013, MIT Probabilistic Computing Project.
* 
* This file is part of Venture.
* 
* Venture is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
* 
* Venture is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
* 
* You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
*/
#include <iostream>
#include <cassert>
#include <cstdlib>
#include <ctime>

#include "node.h"
#include "trace.h"
#include "builtin.h"
#include "sp.h"
#include "omegadb.h"
#include "flush.h"
#include "value.h"
#include "utils.h"
#include "env.h"

#include <boost/range/adaptor/reversed.hpp>

using boost::adaptors::reverse;

Trace::Trace()
{
  gsl_rng_set (rng,time(NULL));
  
  primitivesEnv = new VentureEnvironment;
  for (pair<string,VentureValue *> p : initBuiltInValues()) 
  { primitivesEnv->addBinding(new VentureSymbol(p.first),new Node(NodeType::VALUE,p.second)); }

  for (pair<string,SP *> p : initBuiltInSPs())
  { 
    Node * spNode = new Node(NodeType::VALUE);
    spNode->setValue(new VentureSP(p.second));
    processMadeSP(spNode,false);
    primitivesEnv->addBinding(new VentureSymbol(p.first),spNode);
  }

  globalEnv = new VentureEnvironment(primitivesEnv);

}

Trace::~Trace()
{

  OmegaDB * omegaDB = new OmegaDB;
  map<size_t,pair<Node *,VentureValue*> > orderedFamilies;
  for (unordered_map<size_t, pair<Node *,VentureValue*> >::iterator iter = ventureFamilies.begin(); 
       iter != ventureFamilies.end();
       ++iter)
  { 
    orderedFamilies[iter->first] = iter->second;
  }

  for (map<size_t,pair<Node *,VentureValue*> >::reverse_iterator iter = orderedFamilies.rbegin(); 
       iter != orderedFamilies.rend();
       ++iter)
  {
    Node * root = iter->second.first;
    if (root->isObservation()) 
    { 
      unconstrain(root,true); 
    }
    detachVentureFamily(root,omegaDB); 
    destroyExpression(iter->second.second);
    destroyFamilyNodes(root);
  }

  flushDB(omegaDB,false);

  globalEnv->destroySymbols();
  delete globalEnv;

  for (pair<string,Node*> p : primitivesEnv->frame)
  {
    Node * node = p.second;

    if (dynamic_cast<VentureSP*>(node->getValue()))
    { teardownMadeSP(node,false,omegaDB); }

    delete node->getValue();
    delete node;
  }
  primitivesEnv->destroySymbols();
  delete primitivesEnv;

  for (pair< pair<string,bool >, uint32_t> pp : callCounts)
  {
    if(callCounts[make_pair(pp.first.first,false)] == callCounts[make_pair(pp.first.first,true)]) {
      // OK
    } else {
      cout << "Cleanup mismatch " << pp.first.first << endl;
      cout << callCounts[make_pair(pp.first.first,false)] << " " << callCounts[make_pair(pp.first.first,true)] << endl;
      assert(false);
    }
  }



  gsl_rng_free(rng);

}

void Trace::addApplicationEdges(Node * operatorNode,const vector<Node *> & operandNodes,Node * requestNode, Node * outputNode)
{
  Node::addOperatorEdge(operatorNode,requestNode);
  Node::addOperatorEdge(operatorNode,outputNode);

  Node::addOperandEdges(operandNodes, requestNode);
  Node::addOperandEdges(operandNodes, outputNode);

  Node::addRequestEdge(requestNode, outputNode);
}
