#include "node.h"
#include "value.h"
#include "env.h"
#include "sp.h"
#include "trace.h"
#include "sps/csp.h"
#include "scaffold.h"
#include "particle.h"
#include "srs.h"
#include "flush.h"
#include "lkernel.h"
#include "utils.h"
#include <cmath>

#include <iostream>
#include <typeinfo>
#include "sps/mem.h"

void Trace::commit(Particle * omega)
{
  cout << "Commit!" << endl;

  for (Node * rcNode : omega->randomChoices) { registerRandomChoice(rcNode); }
  for (Node * crcNode : omega->constrainedChoices) { registerConstrainedChoice(crcNode); }
  for (pair<Node *, vector<Node *> > p : omega->esrParents)
  {
    assert(p.first->esrParents.empty());
    p.first->esrParents = p.second;
  }
  
  for (pair<Node *, Node*> p : omega->children)
  {
    p.first->children.insert(p.second);
  }

  for (pair<Node *, Node*> p : omega->sourceNodes) 
  {
    cout << "CommitSourceNode(" << p.first << ") => " << p.second << endl;
    p.first->sourceNode = p.second; 
  }
  for (pair<Node *, Node*> p : omega->lookedUpNodes) { p.first->lookedUpNode = p.second; }

  for (pair<Node *, VentureValue *> p : omega->values) { p.first->setValue(p.second); }
  for (pair<Node *, SPAux *> p : omega->spauxs) { p.first->madeSPAux = p.second; }
}
