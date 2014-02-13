#include "scaffold.h"
#include "node.h"

set<Node *> Scaffold::getPrincipalNodes() { assert(false); }
int Scaffold::getRegenCount(Node * node) { return regenCounts[node]; }
void Scaffold::incRegenCount(Node * node) { regenCounts[node]++; }
void Scaffold::decRegenCount(Node * node) { assert(false); }
bool Scaffold::isResampling(Node * node) { return regenCounts.count(node); }
bool Scaffold::isAbsorbing(Node * node) { return absorbing.count(node); }
bool Scaffold::isAAA(Node * node) { return aaa.count(node); }
bool Scaffold::hasLKernel(Node * node) { return lkernels.count(node); }
shared_ptr<LKernel> Scaffold::getLKernel(Node * node) { assert(false); }

shared_ptr<Scaffold> constructScaffold(Trace * trace,const vector<set<Node*> > & setsOfPNodes) { assert(false); }


void addResamplingNode(Trace * trace,
		       set<Node*> & cDRG,
		       set<Node*> & cAbsorbing,
		       set<Node*> & cAAA,
		       queue<tuple<Node*,bool,Node*> > & q,
		       Node * node,
		       map<Node*,int> & indexAssignments,
		       int i) { assert(false); }

void addAbsorbingNode(set<Node*> & cDRG,
		      set<Node*> & cAbsorbing,
		      set<Node*> & cAAA,
		      Node * node,
		      map<Node*,int> & indexAssignments,
		      int i) { assert(false); }

void addAAANode(set<Node*> & cDRG,
		set<Node*> & cAbsorbing,
		set<Node*> & cAAA,
		Node * node,
		map<Node*,int> & indexAssignments,
		int i) { assert(false); }

void extendCandidateScaffold(ConcreteTrace * trace,
			     const set<Node*> & pnodes,
			     set<Node*> & cDRG,
			     set<Node*> & cAbsorbing,
			     set<Node*> & cAAA,
			     map<Node*,int> & indexAssignments,
			     int i) { assert(false); }

set<Node*> findBrush(ConcreteTrace * trace,
		     set<Node*> & cDRG,
		     set<Node*> & cAbsorbing,
		     set<Node*> & cAAA) { assert(false); }

void disableRequests(ConcreteTrace * trace,
		     Node * node,
		     map<Node*,int> & disableCounts,
		     set<RequestNode*> & disabledRequests,
		     set<Node*> & brush) { assert(false); }

void disableFamily(ConcreteTrace * trace,
		   Node * node,
		   map<Node*,int> & disableCounts,
		   set<RequestNode*> & disabledRequests,
		   set<Node*> & brush) { assert(false); }


tuple<set<Node*>,set<Node*>,set<Node*> > removeBrush(set<Node*> & cDRG,
						     set<Node*> & cAbsorbing,
						     set<Node*> & cAAA,
						     set<Node*> & brush) { assert(false); }

bool hasChildInAorD(ConcreteTrace * trace,
		    set<Node*> & drg,
		    set<Node*> & absorbing,
		    Node * node) { assert(false); }

set<Node*> findBorder(ConcreteTrace * trace,
		      set<Node*> & drg,
		      set<Node*> & absorbing,
		      set<Node*> & aaa) { assert(false); }

void maybeIncrementAAARegenCount(ConcreteTrace * trace,
				 map<Node*,int> & regenCounts,
				 set<Node*> & aaa,
				 Node * node) { assert(false); }

set<Node*> computeRegenCounts(ConcreteTrace * trace,
			      set<Node*> & drg,
			      set<Node*> & absorbing,
			      set<Node*> & aaa,
			      set<Node*> & border,
			      set<Node*> & brush) { assert(false); }

map<Node*,shared_ptr<LKernel> > loadKernels(ConcreteTrace * trace,
					    set<Node*> & drg,
					    set<Node*> & absorbing) { assert(false); }

vector<vector<Node *> > assignBorderSequnce(set<Node*> & border,
					    map<Node*,int> & indexAssignments,
					    int numIndices) { assert(false); }
