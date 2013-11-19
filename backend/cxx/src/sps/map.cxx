#include "sps/map.h"
#include "value.h"

#include "utils.h"
#include "env.h"

#include <iostream>

VentureValue * MakeMapSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  VentureList * keys = dynamic_cast<VentureList*>(args.operands[0]);
  VentureList * values = dynamic_cast<VentureList*>(args.operands[1]);
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

VentureValue * MapContainsSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  VentureMap * vmap = dynamic_cast<VentureMap*>(args.operands[0]);
  assert(vmap);

  return new VentureBool(vmap->map.count(args.operands[1]));
}


VentureValue * MapLookupSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  VentureMap * vmap = dynamic_cast<VentureMap*>(args.operands[0]);
  assert(vmap);

  assert(vmap->map.count(args.operands[1]));
  return vmap->map[args.operands[1]];
}


