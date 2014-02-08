#ifndef TRACE_H
#define TRACE_H

#include "types.h"
#include <set>
#include <map>
#include <vector>
#include "smap.h"

using std::set;
using std::map;
using std::vector;

struct Node;

struct Trace {};

struct ConcreteTrace : Trace
{
  VentureEnvironment * globalEnvironment;
  set<Node*> unconstrainedRandomChoices;
  set<Node*> constrainedChoices;
  set<Node*> arbitraryErgodicKernels;
  set<Node*> unpropagatedObservations;
  map<DirectiveID,RootOfFamily> families;
  map<ScopeID,SMap<BlockID,set<Node*> > scopes;

  map<Node*, vector<Node*> > esrParents;
  map<Node*, int> numRequests;
  map<Node*, SPRecord> madeSPRecords;
  map<Node*,set<Node*> > children;

};

#endif
