#ifndef PARTICLE_H
#define PARTICLE_H

#include <map>

struct Node;
struct SPAux;

struct Particle
{

  void maybeCloneSPAux(Node * node);
  void setSPAuxOverride(Node * node);
  void clearSPAuxOverride(Node * node);

  /* This is new for this particle, 
     and lookup is environment-lookup semantics. 
     For RHO, this is the identity on D and A. */
  map<Node*,VentureValue*> drgDB;

  /* { makerNode => newSPAux } 
     Cloned from parent particle */
  map<Node*,SPAux*> spauxs;

  Particle * parentParticle;
};


#endif
