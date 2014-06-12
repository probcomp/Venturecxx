#ifndef REGEN_H
#define REGEN_H

#include "types.h"

struct Trace;
struct Scaffold;
struct DB;
struct ApplicationNode;
struct OutputNode;
struct RequestNode;
struct VentureEnvironment;

double regenAndAttach(Trace * trace,
		      const vector<Node*> & border,
		      shared_ptr<Scaffold> scaffold,
		      bool shouldRestore,
		      shared_ptr<DB> db,
		      shared_ptr<map<Node*,Gradient> > gradients);

double constrain(Trace * trace,
		 OutputNode * node,
		 VentureValuePtr value);



void propagateConstraint(Trace * trace,
			 Node * node,
			 VentureValuePtr value);

double attach(Trace * trace,
	      ApplicationNode * node,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients);

double regen(Trace * trace,
	      Node * node,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients);

double regenParents(Trace * trace,
	      Node * node,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients);

double regenESRParents(Trace * trace,
	      Node * node,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients);

pair<double,Node*> evalFamily(Trace * trace,
			      VentureValuePtr exp,
			      shared_ptr<VentureEnvironment> env,
			      shared_ptr<Scaffold> scaffold,
			      bool shouldRestore,
			      shared_ptr<DB> db,
			      shared_ptr<map<Node*,Gradient> > gradients);


double apply(Trace * trace,
	      RequestNode * requestNode,
	     OutputNode * outputNode,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients);


void processMadeSP(Trace * trace, Node * node, bool isAAA,bool shouldRestore,shared_ptr<DB> db);

double applyPSP(Trace * trace,
	      ApplicationNode * node,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients);

double evalRequests(Trace * trace,
	      RequestNode * requestNode,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients);

double restore(Trace * trace,
	      Node * node,
	      shared_ptr<Scaffold> scaffold,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients);


#endif
