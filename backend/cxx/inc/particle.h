#ifndef PARTICLE_H
#define PARTICLE_H

#include <map>
#include <set>
#include <vector>
#include <queue>

using namespace std;

#include "flush.h"
#include "args.h"

struct Node;
struct VentureValue;
struct VentureSP;
struct SPAux;

struct Particle
{
  void maybeCloneSPAux(Node * node);
  void maybeCloneMadeSPAux(Node * makerNode);
  void registerSPAux(Node * makerNode,SPAux * freshSPAux);

  SPAux * getSPAux(Node * node);
  SPAux * getMadeSPAux(Node * makerNode);

  SP * sp(Node * node);
  VentureSP * vsp(Node * node);

  void registerReference(Node * node,Node * lookedUpNode);
  bool isReference(Node * node);
  Node * getSourceNode(Node * node);

  VentureValue * getValue(Node * node);
  void setValue(Node * node, VentureValue * value, bool override);
  bool hasValueFor(Node * node);


  void registerConstrainedChoice(Node * node);
  void registerRandomChoice(Node * node);
  void unregisterRandomChoice(Node * node); 
  void unregisterConstrainedChoice(Node * node); 

  Args makeArgs(Node * node);

  set<Node *> randomChoices;
  set<Node *> constrainedChoices;

  // TODO urgent: needs to track this during detach
  multimap<Node *, Node *> children;


  map<Node*,vector<Node*> > esrParents; // not actually necessary, but may be convenient

  map<Node *, Node *> sourceNodes;
  map<Node *, Node *> lookedUpNodes;

  /* This is new for this particle, 
     and lookup is environment-lookup semantics. 
     For RHO, this is the identity on D and Brush. 
     TODO only store values for D here, and store values for the
     brush in the nodes themselves. */
  map<Node*,VentureValue*> values;

  /* { makerNode => newSPAux } 
     Cloned from parent particle */
  map<Node*,SPAux*> spauxs; // the only thing being copied when cloning a particle

  queue<FlushEntry> flushQueue;

  /* TODO once we extend to multiple particles, we will need the following two attributes.
     We are not yet doing the associated bookkeeping for either. */
//  set<Node *> * allNodesOwned;
//  Particle * parentParticle;
};


#endif
