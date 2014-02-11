#ifndef SCAFFOLD_H
#define SCAFFOLD_H

struct Scaffold
{
  set<Node *> getPrincipalNodes();
  int getRegenCount(Node * node);
  void incRegenCount(Node * node);
  void dectRegenCount(Node * node);
  bool isResampling(Node * node);
  bool isAbsorbing(Node * node);
  bool isAAA(Node * node);
  bool hasLKernel(Node * node);
  shared_ptr<LKernel> getLKernel(Node * node);

private:
  vector<set<Node*> > setsOfPNodes;
  map<Node*,int> regenCounts;
  set<Node*> absorbing;
  set<Node*> aaa;
  vector<vector<Node *> > border;
  map<Node*,shared_ptr<LKernel> > lkernels;

};


shared_ptr<Scaffold> constructScaffold(Trace * trace,const vector<set<Node*> > & setsOfPNodes);


// TODO everything from here on should be moved to .cxx
void addResamplingNode(Trace * trace,
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
		     Node * node,
		     map<Node*,int> & disableCounts,
		     set<RequestNode*> & disabledRequests,
		     set<Node*> & brush);

void disableFamily(ConcreteTrace * trace,
		     Node * node,
		     map<Node*,int> & disableCounts,
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

set<Node*> computeRegenCounts(ConcreteTrace * trace,
		    set<Node*> & drg,
		    set<Node*> & absorbing,
			      set<Node*> & aaa,
			      set<Node*> & border,
			      set<Node*> & brush);

map<Node*,shared_ptr<LKernel> > loadKernels(ConcreteTrace * trace,
		    set<Node*> & drg,
					    set<Node*> & absorbing);

vector<vector<Node *> > assignBorderSequnce(set<Node*> & border,
					    map<Node*,int> & indexAssignments,
					    int numIndices);

#endif
