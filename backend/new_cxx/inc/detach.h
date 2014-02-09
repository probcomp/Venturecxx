#ifndef DETACH_H
#define DETACH_H

pair<double,DB*> detachAndExtract(Trace * trace,const vector<Node*> & border,shared_ptr<Scaffold> scaffold);
double unconstrain(Trace * trace,Node * node);
double detach(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,DB * db);
double extractParents(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,DB * db);
double extractESRParents(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,DB * db);
double extract(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,DB * db);
double unevalFamily(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,DB * db);
double unapply(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,DB * db);
void teardownMadeSP(Trace * trace,Node * node,bool isAAA);
double unapplyPSP(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,DB * db);
double unevalRequests(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,DB * db);

#endif
