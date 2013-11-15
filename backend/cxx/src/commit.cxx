#include "node.h"
#include "value.h"
#include "env.h"
#include "sp.h"
#include "trace.h"
#include "sps/csp.h"
#include "scaffold.h"
#include "omegadb.h"
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
  for (Node * rcNode : omega->randomChoices) { registerRandomChoice(rcNode); }
  for (Node * crcNode : omega->constrainedRandomChoices) { registerConstrainedRandomChoice(crcNode); }
  for (pair<Node *, vector<Node *> > p : omega->esrParentns)
  {
    assert(p.first->esrParents.empty());
    p.first->esrParents = p.second;
  }

  for (pair<Node *, Node*> p : omega->sourceNodes) { p.first->sourceNode = p.second; }

  for (pair<Node *, VentureValue *> p : omega->values) { p.first->setValue(p.second); }
  for (pair<Node *, SPAux *> p : omega->spauxs) { p.first->madeSPAux = p.second; }
}
