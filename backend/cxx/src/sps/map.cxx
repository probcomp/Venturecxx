#include "sps/map.h"
#include "value.h"
#include "node.h"
#include "utils.h"
#include "env.h"

#include <iostream>

VentureValue * MakeMapSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  VentureList * keys = dynamic_cast<VentureList*>(node->operandNodes[0]->getValue());
  VentureList * values = dynamic_cast<VentureList*>(node->operandNodes[1]->getValue());
  assert(keys);
  assert(values);

  VentureMap * vmap = new VentureMap;

  while (!dynamic_cast<VentureNil*>(keys))
  {
    VenturePair * pkeys = dynamic_cast<VenturePair*>(keys);
    VenturePair * pvalues = dynamic_cast<VenturePair*>(values);
    assert(pkeys);
    assert(pvalues);
    vmap->map.insert({pkeys->first,pvalues->first});
    keys = pkeys->rest;
    values = pvalues->rest;
  }
  return vmap;
}

VentureValue * MapContainsSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  VentureMap * vmap = dynamic_cast<VentureMap*>(node->operandNodes[0]->getValue());
  assert(vmap);

  return new VentureBool(vmap->map.count(node->operandNodes[1]->getValue()));
}


VentureValue * MapLookupSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  VentureMap * vmap = dynamic_cast<VentureMap*>(node->operandNodes[0]->getValue());
  assert(vmap);

  return vmap->map[node->operandNodes[1]->getValue()];
}


