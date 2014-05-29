#ifndef SCAFFOLD_H
#define SCAFFOLD_H

#include <queue>
#include "boost/tuple/tuple.hpp"
#include "types.h"

using std::queue;
using boost::tuple;
using boost::make_tuple;

struct Trace;
struct LKernel;
struct Node;
struct RequestNode;
struct ConcreteTrace;

struct Scaffold
{
  Scaffold() {}
  Scaffold(const vector<set<Node*> > & setsOfPNodes,
	   const map<Node*,int> & regenCounts,
	   const set<Node*> & absorbing,
	   const set<Node*> & aaa,
	   const vector<vector<Node *> > & border,
	   const map<Node*,shared_ptr<LKernel> > & lkernels,
	   const set<Node*> & brush):
  setsOfPNodes(setsOfPNodes),
    regenCounts(regenCounts),
    absorbing(absorbing),
    aaa(aaa),
    border(border),
    lkernels(lkernels),
    brush(brush)
          {}
  

  set<Node *> getPrincipalNodes();
  Node * getPrincipalNode();
  int getRegenCount(Node * node);
  void incRegenCount(Node * node);
  void decRegenCount(Node * node);
  bool isResampling(Node * node);
  bool isAbsorbing(Node * node);
  bool isAAA(Node * node);
  bool hasLKernel(Node * node);
  void registerLKernel(Node * node,shared_ptr<LKernel> lkernel);
  shared_ptr<LKernel> getLKernel(Node * node);
  string showSizes();


  vector<set<Node*> > setsOfPNodes;
  map<Node*,int> regenCounts;
  set<Node*> absorbing;
  set<Node*> aaa;
  vector<vector<Node *> > border;
  map<Node*,shared_ptr<LKernel> > lkernels;
  set<Node*> brush;

};


shared_ptr<Scaffold> constructScaffold(ConcreteTrace * trace,const vector<set<Node*> > & setsOfPNodes,bool useDeltaKernels);

// TODO everything from here on should be moved to .cxx
void addResamplingNode(ConcreteTrace * trace,
            set<Node*> & cDRG,
			      set<Node*> & cAbsorbing,
			      set<Node*> & cAAA,
			      queue<tuple<Node*,bool,Node*> > & q,
			      Node * node,
			      map<Node*,int> & indexAssignments,
			      int i);

void addAbsorbingNode(set<Node*> & cDRG,
			      set<Node*> & cAbsorbing,
			      set<Node*> & cAAA,
			      Node * node,
			      map<Node*,int> & indexAssignments,
			      int i);

void addAAANode(set<Node*> & cDRG,
			      set<Node*> & cAbsorbing,
			      set<Node*> & cAAA,
			      Node * node,
			      map<Node*,int> & indexAssignments,
			      int i);

void extendCandidateScaffold(ConcreteTrace * trace,
			     const set<Node*> & pnodes,
			     set<Node*> & cDRG,
			     set<Node*> & cAbsorbing,
			     set<Node*> & cAAA,
			     map<Node*,int> & indexAssignments,
			     int i);

set<Node*> findBrush(ConcreteTrace * trace,
		     set<Node*> & cDRG,
		     set<Node*> & cAbsorbing,
		     set<Node*> & cAAA);

void disableRequests(ConcreteTrace * trace,
		     RequestNode * node,
		     map<RootOfFamily,int> & disableCounts,
		     set<RequestNode*> & disabledRequests,
		     set<Node*> & brush);

void disableFamily(ConcreteTrace * trace,
		     Node * node,
		     map<RootOfFamily,int> & disableCounts,
		     set<RequestNode*> & disabledRequests,
		     set<Node*> & brush);


tuple<set<Node*>,set<Node*>,set<Node*> > removeBrush(set<Node*> & cDRG,
						     set<Node*> & cAbsorbing,
						     set<Node*> & cAAA,
						     set<Node*> & brush);

bool hasChildInAorD(ConcreteTrace * trace,
		    set<Node*> & drg,
		    set<Node*> & absorbing,
		    Node * node);

set<Node*> findBorder(ConcreteTrace * trace,
		    set<Node*> & drg,
		    set<Node*> & absorbing,
		      set<Node*> & aaa);

void maybeIncrementAAARegenCount(ConcreteTrace * trace,
				 map<Node*,int> & regenCounts,
				 set<Node*> & aaa,
				 Node * node);

map<Node*,int> computeRegenCounts(ConcreteTrace * trace,
		    set<Node*> & drg,
		    set<Node*> & absorbing,
			      set<Node*> & aaa,
			      set<Node*> & border,
			      set<Node*> & brush);

map<Node*,shared_ptr<LKernel> > loadKernels(ConcreteTrace * trace,
					    set<Node*> & drg,
					    set<Node*> & aaa,
					    bool useDeltaKernels);

vector<vector<Node *> > assignBorderSequnce(set<Node*> & border,
					    map<Node*,int> & indexAssignments,
					    int numIndices);

#endif
