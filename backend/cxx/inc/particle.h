#ifnef PARTICLE_H
#define PARTICLE_H

struct Particle
{
  /* OLD, now we leave the topology of the old trace alone, so that it is easier to 
     walk it during regen. */
     
  /* { OldNode => NewNode }
     This is new for this particle, 
     and lookup is environment-lookup semantics. 
     For RHO, this is the identity on D but we actually copy A, for symmetry.
     Since we disconnect RHO from the trace on the other end as well, no particle
     fills the torus during the proposal. */
  map<Node*,Node*> newNodes;

  /* { makerNode => newSPAux } 
     Cloned from parent particle */
  map<Node*,SPAux*> spauxs;

  /* { newNode => (old/new) node that has newNode as child,
                  but whose children do not include it yet. } 
     New for this particle, but we iterate over ancestors when
     actually adding these missing edges. 
     Note: for simplicity, we actually use this same structure
           for RHO as well, since we disconnect children of the parents
	   of nodes in R(rho) during detach, so that no nodes in RHO or XI
	   are pointed to by the parents.
   */
  map<Node*,set<Node*> > missingChildren; // for XI, from D => parents in I
  map<Node*,set<Node*> > missingParents; // for XI, from D => children in A

  map<Node*,set<Node*> > extraChildren; // for RHO only, for parents in I => D
  map<Node*,set<Node*> > extraParents; // for RHO only, for A => parents in D

  /* Note: missing parents will be handled by inspecting the parents of
     the NEW absorbing nodes in a given particle. */

  Particle * parentParticle;
};


#endif
