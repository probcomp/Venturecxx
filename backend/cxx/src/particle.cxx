#include "particle.h"
#include "node.h"
#include "spaux.h"

void Particle::maybeCloneSPAux(Node * node)
{
  Node * makerNode = node->vsp()->makerNode;
  if (makerNode->madeSPAux && !spauxs.count(makerNode))
  {
    spauxs[makerNode] = makerNode->madeSPAux->clone();
  }
}

void Particle::maybeCloneSPAux(Node * makerNode)
{
  if (makerNode->madeSPAux && !spauxs.count(makerNode))
  {
    spauxs[makerNode] = makerNode->madeSPAux->clone();
  }
}


