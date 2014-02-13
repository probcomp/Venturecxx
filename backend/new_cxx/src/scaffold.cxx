#include "scaffold.h"
#include "node.h"

set<Node *> Scaffold::getPrincipalNodes() { assert(false); }

int Scaffold::getRegenCount(Node * node) 
{ 
  assert(regenCounts.count(node));
  assert(regenCounts[node] >= 0);
  return regenCounts[node]; 
}

void Scaffold::incRegenCount(Node * node) 
{
  assert(regenCounts.count(node));
  regenCounts[node]++; 
}

void Scaffold::decRegenCount(Node * node) 
{ 
  assert(regenCounts.count(node));
  regenCounts[node]--;
  assert(regenCounts[node] >= 0);
}

bool Scaffold::isResampling(Node * node) { return regenCounts.count(node); }
bool Scaffold::isAbsorbing(Node * node) { return absorbing.count(node); }
bool Scaffold::isAAA(Node * node) { return aaa.count(node); }
bool Scaffold::hasLKernel(Node * node) { return lkernels.count(node); }

shared_ptr<LKernel> Scaffold::getLKernel(Node * node) { assert(false); }


shared_ptr<Scaffold> constructScaffold(ConcreteTrace * trace,const vector<set<Node*> > & setsOfPNodes)
{
  set<Node*> cDRG;
  set<Node*> cAbsorbing;
  set<Node*> cAAA;
  map<Node*,int> indexAssignments;

  for (size_t i = 0; i < setsOfPNodes.size(); ++i)
  {
    extendCandidateScaffold(trace,setsOfPNodes[i],cDRG,cAbsorbing,cAAA,indexAssignments,i);
  }
  set<Node*> brush = findBrush(trace,cDRG,cAbsorbing,cAAA);
  tuple<set<Node*>,set<Node*>,set<Node*> > coreScaffold  = removeBrush(cDRG,cAbsorbing,cAAA,brush);
  set<Node*> drg = boost::get<0>(coreScaffold);
  set<Node*> absorbing = boost::get<1>(coreScaffold);
  set<Node*> aaa = boost::get<2>(coreScaffold);

  set<Node*> border = findBorder(trace,drg,absorbing,aaa);
  map<Node*,int> regenCounts = computeRegenCounts(trace,drg,absorbing,aaa,border,brush);
  map<Node*,shared_ptr<LKernel> > lkernels = loadKernels(trace,drg,aaa);
  vector<vector<Node *> > borderSequence = assignBorderSequnce(border,indexAssignments,setsOfPNodes.size());
  return shared_ptr<Scaffold>(new Scaffold(setsOfPNodes,regenCounts,absorbing,aaa,borderSequence,lkernels));
}


void addResamplingNode(ConcreteTrace * trace,
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

map<Node*,int> computeRegenCounts(ConcreteTrace * trace,
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
