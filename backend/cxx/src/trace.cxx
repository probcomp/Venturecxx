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

#include <boost/range/adaptor/reversed.hpp>

using boost::adaptors::reverse;

Trace::Trace()
{
  gsl_rng_set (rng,time(NULL));
  
  Environment primitivesEnv;
  for (pair<string,VentureValue *> p : initBuiltInValues()) 
  { primitivesEnv.addBinding(p.first,new Node(NodeType::VALUE,p.second)); }

  for (pair<string,SP *> p : initBuiltInSPs())
  { 
    Node * spNode = new Node(NodeType::VALUE);
    spNode->setValue(new VentureSP(spNode,p.second));
    processMadeSP(spNode);
    primitivesEnv.addBinding(p.first,spNode);
  }

  Node * primitivesEnvNode = new Node(NodeType::VALUE,new VentureEnvironment(primitivesEnv));

  Environment globalEnv(primitivesEnvNode);
  globalEnvNode = new Node(NodeType::VALUE,new VentureEnvironment(globalEnv));
}

Trace::~Trace()
{
  vector<VentureValue *> observedValues;
  for (map<size_t, Node *>::reverse_iterator iter = ventureFamilies.rbegin(); 
       iter != ventureFamilies.rend();
       ++iter)
  { 
    OmegaDB omegaDB;
    Node * root = ventureFamilies[iter->first];
    if (root->isObservation()) 
    { 
      observedValues.push_back(root->getValue());
      unconstrain(root); 
    }
    detachVentureFamily(ventureFamilies[iter->first],omegaDB); 
    flushDB(omegaDB);
    destroyFamilyNodes(root);
  }

  for (VentureValue * obs : observedValues) { delete obs; }

  /* Now use the global environment to destroy all of the primitives. */
  Node * primitivesEnvNode = globalEnvNode->getEnvironment()->outerEnvNode;
  delete globalEnvNode->getValue();
  delete globalEnvNode;

  for (pair<string,Node*> p : primitivesEnvNode->getEnvironment()->frame)
  {
    Node * node = p.second;
    if (node->madeSPAux) 
    { 
      VentureSP * vvsp = dynamic_cast<VentureSP*>(node->getValue());
      assert(vvsp);
      vvsp->sp->destroySPAux(node->madeSPAux);
    }
    delete node->getValue();
    delete node;
  }
  delete primitivesEnvNode->getValue();
  delete primitivesEnvNode;

}

void Trace::addApplicationEdges(Node * operatorNode,const vector<Node *> & operandNodes,Node * requestNode, Node * outputNode)
{
  Node::addOperatorEdge(operatorNode,requestNode);
  Node::addOperatorEdge(operatorNode,outputNode);

  Node::addOperandEdges(operandNodes, requestNode);
  Node::addOperandEdges(operandNodes, outputNode);

  Node::addRequestEdge(requestNode, outputNode);
}
