#ifndef DETACH_H
#define DETACH_H

#include "types.h"

struct Trace;
struct Scaffold;
struct DB;
struct Node;
struct ApplicationNode;
struct OutputNode;
struct RequestNode;

pair<double,shared_ptr<DB> > detachAndExtract(Trace * trace,const vector<Node*> & border,shared_ptr<Scaffold> scaffold);
double unconstrain(Trace * trace,Node * node);
double detach(Trace * trace,ApplicationNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db);
double extractParents(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db);
double extractESRParents(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db);
double extract(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db);
double unevalFamily(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db);
double unapply(Trace * trace,OutputNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db);
void teardownMadeSP(Trace * trace,Node * node,bool isAAA);
double unapplyPSP(Trace * trace,ApplicationNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db);
double unevalRequests(Trace * trace,RequestNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db);

#endif
