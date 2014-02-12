#include "scaffold.h"
#include "node.h"

set<Node *> Scaffold::getPrincipalNodes() { throw 500; }
int Scaffold::getRegenCount(Node * node) { throw 500; }
void Scaffold::incRegenCount(Node * node) { throw 500; }
void Scaffold::decRegenCount(Node * node) { throw 500; }
bool Scaffold::isResampling(Node * node) { throw 500; }
bool Scaffold::isAbsorbing(Node * node) { throw 500; }
bool Scaffold::isAAA(Node * node) { throw 500; }
bool Scaffold::hasLKernel(Node * node) { throw 500; }
shared_ptr<LKernel> Scaffold::getLKernel(Node * node) { throw 500; }

shared_ptr<Scaffold> constructScaffold(Trace * trace,const vector<set<Node*> > & setsOfPNodes) { throw 500; }


void addResamplingNode(Trace * trace,
		       set<Node*> & cDRG,
		       set<Node*> & cAbsorbing,
		       set<Node*> & cAAA,
		       queue<tuple<Node*,bool,Node*> > & q,
		       Node * node,
		       map<Node*,int> & indexAssignments,
		       int i) { throw 500; }

void addAbsorbingNode(set<Node*> & cDRG,
		      set<Node*> & cAbsorbing,
		      set<Node*> & cAAA,
		      Node * node,
		      map<Node*,int> & indexAssignments,
		      int i) { throw 500; }

void addAAANode(set<Node*> & cDRG,
		set<Node*> & cAbsorbing,
		set<Node*> & cAAA,
		Node * node,
		map<Node*,int> & indexAssignments,
		int i) { throw 500; }

void extendCandidateScaffold(ConcreteTrace * trace,
			     const set<Node*> & pnodes,
			     set<Node*> & cDRG,
			     set<Node*> & cAbsorbing,
			     set<Node*> & cAAA,
			     map<Node*,int> & indexAssignments,
			     int i) { throw 500; }

set<Node*> findBrush(ConcreteTrace * trace,
		     set<Node*> & cDRG,
		     set<Node*> & cAbsorbing,
		     set<Node*> & cAAA) { throw 500; }

void disableRequests(ConcreteTrace * trace,
		     Node * node,
		     map<Node*,int> & disableCounts,
		     set<RequestNode*> & disabledRequests,
		     set<Node*> & brush) { throw 500; }

void disableFamily(ConcreteTrace * trace,
		   Node * node,
		   map<Node*,int> & disableCounts,
		   set<RequestNode*> & disabledRequests,
		   set<Node*> & brush) { throw 500; }


tuple<set<Node*>,set<Node*>,set<Node*> > removeBrush(set<Node*> & cDRG,
						     set<Node*> & cAbsorbing,
						     set<Node*> & cAAA,
						     set<Node*> & brush) { throw 500; }

bool hasChildInAorD(ConcreteTrace * trace,
		    set<Node*> & drg,
		    set<Node*> & absorbing,
		    Node * node) { throw 500; }

set<Node*> findBorder(ConcreteTrace * trace,
		      set<Node*> & drg,
		      set<Node*> & absorbing,
		      set<Node*> & aaa) { throw 500; }

void maybeIncrementAAARegenCount(ConcreteTrace * trace,
				 map<Node*,int> & regenCounts,
				 set<Node*> & aaa,
				 Node * node) { throw 500; }

set<Node*> computeRegenCounts(ConcreteTrace * trace,
			      set<Node*> & drg,
			      set<Node*> & absorbing,
			      set<Node*> & aaa,
			      set<Node*> & border,
			      set<Node*> & brush) { throw 500; }

map<Node*,shared_ptr<LKernel> > loadKernels(ConcreteTrace * trace,
					    set<Node*> & drg,
					    set<Node*> & absorbing) { throw 500; }

vector<vector<Node *> > assignBorderSequnce(set<Node*> & border,
					    map<Node*,int> & indexAssignments,
					    int numIndices) { throw 500; }
