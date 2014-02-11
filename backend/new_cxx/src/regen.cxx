double regenAndAttach(Trace * trace,
		      const vector<Node*> & border,
		      shared_ptr<Scaffold> scaffold,
		      bool shouldRestore,
		      shared_ptr<DB> db,
		      shared_ptr<map<Node*,Gradient> > gradients)
{ throw 500; }

double constrain(Trace * trace,
		 Node * node,
		 VentureValuePtr value)
{ throw 500; }



void propagateConstraint(Trace * trace,
			 Node * node,
			 VentureValuePtr value)
{ throw 500; }

double attach(Trace * trace,
	      Node * node,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{ throw 500; }

double regen(Trace * trace,
	      Node * node,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{ throw 500; }

double regenParents(Trace * trace,
	      Node * node,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{ throw 500; }

double regenESRParents(Trace * trace,
	      Node * node,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{ throw 500; }

pair<double,Node*> evalFamily(Trace * trace,
			      VentureValuePtr exp,
			      shared_ptr<VentureEnvironment> env,
			      shared_ptr<Scaffold> scaffold,
			      bool shouldRestore,
			      shared_ptr<DB> db,
			      shared_ptr<map<Node*,Gradient> > gradients)
{ throw 500; }


double apply(Trace * trace,
	      RequestNode * requestNode,
	     OutputNode * outputNode,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{ throw 500; }


void processMadeSP(Trace * trace, Node * node, bool isAAA)
{ throw 500; }

double applyPSP(Trace * trace,
	      Node * node,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{ throw 500; }

double evalRequests(Trace * trace,
	      RequestNode * requestNode,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{ throw 500; }

double restore(Trace * trace,
	      RequestNode * requestNode,
	      shared_ptr<Scaffold> scaffold,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{ throw 500; }
