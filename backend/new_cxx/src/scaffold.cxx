#include "scaffold.h"
#include "node.h"
#include "concrete_trace.h"
#include "sp.h"
#include <algorithm>

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
		       int i)
{
  if (cAbsorbing.count(node)) { cAbsorbing.erase(node); }
  if (cAAA.count(node)) { cAAA.erase(node); }
  cDRG.insert(node);
  set<Node*> children = trace->getChildren(node);
  for (set<Node*>::iterator childIter = children.begin();
       childIter != children.end();
       ++childIter)
  {
    q.push(make_tuple(*childIter,false,node));
  }
  indexAssignments[node] = i;
}

void addAbsorbingNode(set<Node*> & cDRG,
		      set<Node*> & cAbsorbing,
		      set<Node*> & cAAA,
		      Node * node,
		      map<Node*,int> & indexAssignments,
		      int i) 
{
  assert(!cDRG.count(node));
  assert(!cAAA.count(node));
  cAbsorbing.insert(node);
  indexAssignments[node] = i;
}

void addAAANode(set<Node*> & cDRG,
		set<Node*> & cAbsorbing,
		set<Node*> & cAAA,
		Node * node,
		map<Node*,int> & indexAssignments,
		int i) 
{
  if (cAbsorbing.count(node)) { cAbsorbing.erase(node); }
  cDRG.insert(node);
  cAAA.insert(node);
  indexAssignments[node] = i;
}

void extendCandidateScaffold(ConcreteTrace * trace,
			     const set<Node*> & pnodes,
			     set<Node*> & cDRG,
			     set<Node*> & cAbsorbing,
			     set<Node*> & cAAA,
			     map<Node*,int> & indexAssignments,
			     int i) 
{
  queue<tuple<Node*,bool,Node*> > q;
  for (set<Node*>::iterator pnodeIter = pnodes.begin();
       pnodeIter != pnodes.end();
       ++pnodeIter)
  {
    Node * nullNode = NULL;
    q.push(make_tuple(*pnodeIter,true,nullNode));
  }

  while (!q.empty())
  {
    tuple<Node*,bool,Node*> qElem = q.front();
    Node * node = boost::get<0>(qElem);
    bool isPrincipal = boost::get<1>(qElem);
    Node * parentNode = boost::get<2>(qElem);
    q.pop();

    if (cDRG.count(node) && !cAAA.count(node)) { }
    else if (dynamic_cast<LookupNode*>(node))
    {
      addResamplingNode(trace,cDRG,cAbsorbing,cAAA,q,node,indexAssignments,i);
    }
    else
    {
      ApplicationNode * appNode = dynamic_cast<ApplicationNode*>(node);
      assert(appNode);
      shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(appNode))->getPSP(appNode);
      if (cDRG.count(appNode->operatorNode))
      {
	addResamplingNode(trace,cDRG,cAbsorbing,cAAA,q,node,indexAssignments,i);
      }
      else if (cAAA.count(appNode)) { }
      else if (!isPrincipal && psp->canAbsorb(trace,appNode,parentNode))
      {
	addAbsorbingNode(cDRG,cAbsorbing,cAAA,appNode,indexAssignments,i);
      }
      else if (psp->childrenCanAAA())
      {
	addAAANode(cDRG,cAbsorbing,cAAA,node,indexAssignments,i);
      }
      else 
      { 
	addResamplingNode(trace,cDRG,cAbsorbing,cAAA,q,node,indexAssignments,i); 
      }
    }
  }
}

set<Node*> findBrush(ConcreteTrace * trace,
		     set<Node*> & cDRG,
		     set<Node*> & cAbsorbing,
		     set<Node*> & cAAA) 
{
  map<RootOfFamily,int> disableCounts;
  set<RequestNode*> disabledRequests;
  set<Node*> brush;
  for (set<Node*>::iterator drgIter = cDRG.begin();
       drgIter != cDRG.end();
       ++drgIter)
  {
    RequestNode * requestNode = dynamic_cast<RequestNode*>(*drgIter);
    if (requestNode) { disableRequests(trace,requestNode,disableCounts,disabledRequests,brush); }
  }
  return brush;
}

void disableRequests(ConcreteTrace * trace,
		     RequestNode * node,
		     map<RootOfFamily,int> & disableCounts,
		     set<RequestNode*> & disabledRequests,
		     set<Node*> & brush)
{
  if (disabledRequests.count(node)) { return; }
  disabledRequests.insert(node);
  vector<RootOfFamily> esrRoots = trace->getESRParents(node->outputNode);
  for (size_t i = 0; i < esrRoots.size(); ++i) 
  { 
    RootOfFamily esrRoot = esrRoots[i];
    disableCounts[esrRoot] += 1;
    if (disableCounts[esrRoot] == trace->getNumRequests(esrRoot))
    {
      disableFamily(trace,esrRoot.get(),disableCounts,disabledRequests,brush);
    }
  }
}


void disableFamily(ConcreteTrace * trace,
		   Node * node,
		   map<RootOfFamily,int> & disableCounts,
		   set<RequestNode*> & disabledRequests,
		   set<Node*> & brush) 
{
  if (brush.count(node)){ return; }
  brush.insert(node);
  OutputNode * outputNode = dynamic_cast<OutputNode*>(node);
  if (outputNode)
  {
    brush.insert(outputNode->requestNode);
    disableRequests(trace,outputNode->requestNode,disableCounts,disabledRequests,brush);
    disableFamily(trace,outputNode->operatorNode,disableCounts,disabledRequests,brush);
    for (size_t i = 0; i < outputNode->operandNodes.size(); ++i)
    {
      disableFamily(trace,outputNode->operandNodes[i],disableCounts,disabledRequests,brush);
    }
  }
}


tuple<set<Node*>,set<Node*>,set<Node*> > removeBrush(set<Node*> & cDRG,
						     set<Node*> & cAbsorbing,
						     set<Node*> & cAAA,
						     set<Node*> & brush) 
{
  set<Node*> drg;
  set<Node*> absorbing;
  set<Node*> aaa;

  // TODO confirm that this works
  std::set_difference(cDRG.begin(),cDRG.end(),brush.begin(),brush.end(), 
		      std::inserter(drg,drg.begin()));

  std::set_difference(cAbsorbing.begin(),cAbsorbing.end(),brush.begin(),brush.end(), 
		      std::inserter(absorbing,absorbing.begin()));

  std::set_difference(cAAA.begin(),cAAA.end(),brush.begin(),brush.end(), 
		      std::inserter(aaa,aaa.begin()));

  /* DEBUG */
  assert(std::includes(aaa.begin(),aaa.end(),drg.begin(),drg.end()));
  set<Node*> intersection;
  set_intersection(drg.begin(),drg.end(),absorbing.begin(),absorbing.end(), std::inserter(intersection,intersection.begin()));
  assert(intersection.empty());
  /* END DEBUG */

  return make_tuple(drg,absorbing,aaa);
}

bool hasChildInAorD(ConcreteTrace * trace,
		    set<Node*> & drg,
		    set<Node*> & absorbing,
		    Node * node) 
{
  set<Node *> children = trace->getChildren(node);
  for (set<Node*>::iterator childIter = children.begin();
       childIter != children.end();
       ++childIter)
  {
    if (drg.count(*childIter) || absorbing.count(*childIter)) { return true; }
  }
  return false;
}

set<Node*> findBorder(ConcreteTrace * trace,
		      set<Node*> & drg,
		      set<Node*> & absorbing,
		      set<Node*> & aaa) 
{
  set<Node*> border;
  std::set_union(absorbing.begin(),absorbing.end(),aaa.begin(),aaa.end(), 
		 std::inserter(border,border.begin()));
  for (set<Node*>::iterator drgIter = drg.begin(); drgIter != drg.end(); ++drgIter)
  {
    if (!hasChildInAorD(trace,drg,absorbing,*drgIter)) { border.insert(*drgIter); }
  }
  return border;
}

void maybeIncrementAAARegenCount(ConcreteTrace * trace,
				 map<Node*,int> & regenCounts,
				 set<Node*> & aaa,
				 Node * node) 
{
  shared_ptr<VentureSPRef> spRef = dynamic_pointer_cast<VentureSPRef>(trace->getValue(node));
  if (spRef && aaa.count(spRef->makerNode)) { regenCounts[spRef->makerNode] += 1; }
}

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
