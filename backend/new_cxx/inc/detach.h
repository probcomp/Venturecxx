#ifndef DETACH_H
#define DETACH_H

#include "types.h"

struct ConcreteTrace;
struct Scaffold;
struct DB;
struct Node;
struct ApplicationNode;
struct OutputNode;
struct RequestNode;

pair<double,shared_ptr<DB> > detachAndExtract(ConcreteTrace * trace,const vector<Node*> & border,shared_ptr<Scaffold> scaffold, bool compute_gradient = false);
double unconstrain(ConcreteTrace * trace,OutputNode * node);
double detach(ConcreteTrace * trace,ApplicationNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db, bool compute_gradient = false);
double extractParents(ConcreteTrace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db, bool compute_gradient = false);
double extractESRParents(ConcreteTrace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db, bool compute_gradient = false);
double extract(ConcreteTrace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db, bool compute_gradient = false);
double unevalFamily(ConcreteTrace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db, bool compute_gradient = false);
double unapply(ConcreteTrace * trace,OutputNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db, bool compute_gradient = false);
void teardownMadeSP(ConcreteTrace * trace,Node * node,bool isAAA,shared_ptr<DB> db);
double unapplyPSP(ConcreteTrace * trace,ApplicationNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db, bool compute_gradient = false);
double unevalRequests(ConcreteTrace * trace,RequestNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db, bool compute_gradient = false);

#endif
