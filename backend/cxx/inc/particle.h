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

  /* This is new for this particle, 
     and lookup is environment-lookup semantics. 
     For RHO, this is the identity on D and A. */
  map<Node*,VentureValue*> drgDB;

  /* { makerNode => newSPAux } 
     Cloned from parent particle */
  map<Node*,SPAux*> spauxs;

  queue<FlushEntry> flushQueue;

  Particle * parentParticle;
};


#endif
