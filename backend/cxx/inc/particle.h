#ifndef PARTICLE_H
#define PARTICLE_H

#include <map>
#include <unordered_map>
#include <vector>
#include <queue>

using namespace std;

#include "flush.h"

struct Node;
struct VentureValue;
struct SPAux;

struct Particle
{
  void maybeCloneSPAux(Node * node);
  void maybeCloneMadeSPAux(Node * makerNode);
  void registerSPAux(Node * makerNode,SPAux * freshSPAux);

  SPAux * getSPAux(Node * node);
  SPAux * getMadeSPAux(Node * makerNode);

  SP * sp(Node * node);

  bool isReference(Node * node);
  Node * getSourceNode(Node * node);

  VentureValue * getValue(Node * node);
  void setValue(Node * node, VentureValue * value);
  bool hasValueFor(Node * node);

  void unregisterRandomChoice(Node * node); 
  void registerConstrainedChoice(Node * node);

  Args makeArgs(Node * node);

  set<Node *> randomChoices;
  set<Node *> constrainedRandomChoices;

  map<Node*,vector<Node*> > esrParents; // not actually necessary, but may be convenient
  map<Node *, Node *> sourceNodes;

  /* This is new for this particle, 
     and lookup is environment-lookup semantics. 
     For RHO, this is the identity on D and A. */
  map<Node*,VentureValue*> values;

  /* { makerNode => newSPAux } 
     Cloned from parent particle */
  map<Node*,SPAux*> spauxs;

  queue<FlushEntry> flushQueue;

  /* TODO once we extend to multiple particles, we will need the following two attributes.
     We are not yet doing the associated bookkeeping for either. */
//  set<Node *> * allNodesOwned;
//  Particle * parentParticle;
};


#endif
