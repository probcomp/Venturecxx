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

  /* { nodeInR => (old/new) node that has newNode as child,
                  but whose children do not include it yet. } 
     New for this particle, but we iterate over ancestors when
     actually adding these missing edges. 
     This consists of two types of mappings:
     For RHO, we add to this whenever we remove an ESR edge or disconnect a lookup.
              in both cases, we only remove the CHILD, not the PARENT
	      also, we do not disconnect regular parents of nodes in D.
     For XI, we add to this whenever we add parents to a new node, which includes ESRs,
             lookups, and regular parents.
  */
  map<Node*,set<Node*> > missingChildren;

  /* { oldAbsorbiNode => newNode }, only applies to XI. */
  map<Node*,set<Node*> > missingParents;

  /* { parent => oldRhoNode that would need to be removed from children. }
     We only need to do this for parents in I, but it may be easier to do it for
     all parents, in D as well. */
  map<Node*,set<Node*> > extraChildren;

  /* { oldAbsorbiNode => oldNode } */
  map<Node*,set<Node*> > extraParents; // for RHO only, for A => parents in D

  
  vector<Node *> unconstrainedRandomChoices;
  /* Set, because we do not add to unconstrainedRandomChoices if it is constrained,
     and unconstrain visits first. */
  set<Node *> constrainedChoices;

  Particle * parentParticle;
};


#endif
