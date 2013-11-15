#ifnef PARTICLE_H
#define PARTICLE_H

struct Particle
{
  /* { OldNode => NewNode }
     This is new for this particle, 
     and lookup is environment-lookup semantics. 
     For RHO, this is the identity on D and A. */
  map<Node*,Node*> newNodes;

  /* { makerNode => newSPAux } 
     Cloned from parent particle */
  map<Node*,SPAux*> spauxs;

  Particle * parentParticle;
};


#endif
