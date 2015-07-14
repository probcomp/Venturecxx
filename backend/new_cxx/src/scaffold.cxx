// Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

#include "scaffold.h"
#include "node.h"
#include "concrete_trace.h"
#include "sp.h"
#include <algorithm>
#include <boost/lexical_cast.hpp>
#include <boost/foreach.hpp>

set<Node *> Scaffold::getPrincipalNodes() 
{ 
  assert(setsOfPNodes.size() == 1);
  return setsOfPNodes[0];
}

Node * Scaffold::getPrincipalNode()
{
  assert(setsOfPNodes.size() == 1);
  assert(setsOfPNodes[0].size() == 1);
  BOOST_FOREACH(Node * pnode , setsOfPNodes[0]) { return pnode; }
  assert(false);
  return NULL;
}

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
void Scaffold::registerLKernel(Node * node,boost::shared_ptr<LKernel> lkernel) { lkernels[node] = lkernel; }

boost::shared_ptr<LKernel> Scaffold::getLKernel(Node * node) 
{
  assert(lkernels.count(node));
  return lkernels[node];
}

string Scaffold::showSizes()
{
  string p = "(";
  return p + boost::lexical_cast<string>(regenCounts.size()) + "," + boost::lexical_cast<string>(absorbing.size()) + "," + boost::lexical_cast<string>(aaa.size()) + "," + boost::lexical_cast<string>(border[0].size()) + "," + boost::lexical_cast<string>(brush.size()) + ")";
}


boost::shared_ptr<Scaffold> constructScaffold(ConcreteTrace * trace,const vector<set<Node*> > & setsOfPNodes,bool useDeltaKernels)
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
  map<Node*,boost::shared_ptr<LKernel> > lkernels = loadKernels(trace,drg,aaa,false);
  vector<vector<Node *> > borderSequence = assignBorderSequnce(border,indexAssignments,setsOfPNodes.size());
  return boost::shared_ptr<Scaffold>(new Scaffold(setsOfPNodes,regenCounts,absorbing,aaa,borderSequence,lkernels,brush));
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
      boost::shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(appNode))->getPSP(appNode);
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
  // assert(std::includes(aaa.begin(),aaa.end(),drg.begin(),drg.end()));
  // set<Node*> intersection;
  // set_intersection(drg.begin(),drg.end(),absorbing.begin(),absorbing.end(), std::inserter(intersection,intersection.begin()));
  // assert(intersection.empty());
  /* END DEBUG */

  return tuple<set<Node*>,set<Node*>,set<Node*> >(drg,absorbing,aaa);
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
  boost::shared_ptr<VentureSPRef> spRef = dynamic_pointer_cast<VentureSPRef>(trace->getValue(node));
  if (spRef && aaa.count(spRef->makerNode)) { regenCounts[spRef->makerNode] += 1; }
}

map<Node*,int> computeRegenCounts(ConcreteTrace * trace,
                                  set<Node*> & drg,
                                  set<Node*> & absorbing,
                                  set<Node*> & aaa,
                                  set<Node*> & border,
                                  set<Node*> & brush) 
{
  map<Node*,int> regenCounts;
  for (set<Node*>::iterator drgIter = drg.begin(); drgIter != drg.end(); ++drgIter)
  {
    if (aaa.count(*drgIter)) { regenCounts[*drgIter] = 1; } // will be added to shortly
    else if (border.count(*drgIter)) { regenCounts[*drgIter] = trace->getChildren(*drgIter).size() + 1; }
    else { regenCounts[*drgIter] = trace->getChildren(*drgIter).size(); }
  }

  if (!aaa.empty())
  {
    for (set<Node*>::iterator drgIter = drg.begin(); drgIter != drg.end(); ++drgIter)
    {
      vector<Node*> parents = trace->getParents(*drgIter);
      for (size_t i = 0; i < parents.size(); ++i) { maybeIncrementAAARegenCount(trace,regenCounts,aaa,parents[i]); }
    }

    for (set<Node*>::iterator absorbingIter = absorbing.begin(); absorbingIter != absorbing.end(); ++absorbingIter)
    {
      vector<Node*> parents = trace->getParents(*absorbingIter);
      for (size_t i = 0; i < parents.size(); ++i) { maybeIncrementAAARegenCount(trace,regenCounts,aaa,parents[i]); }
    }
    
    for (set<Node*>::iterator brushIter = brush.begin(); brushIter != brush.end(); ++brushIter)
    {
      LookupNode * lookupNode = dynamic_cast<LookupNode*>(*brushIter);
      OutputNode * outputNode = dynamic_cast<OutputNode*>(*brushIter);
      if (outputNode) 
      {
        vector<RootOfFamily> esrParents = trace->getESRParents(*brushIter);
        for (size_t i = 0; i < esrParents.size(); ++i) { maybeIncrementAAARegenCount(trace,regenCounts,aaa,esrParents[i].get()); }
      }
      if (lookupNode)
      {
        maybeIncrementAAARegenCount(trace,regenCounts,aaa,lookupNode->sourceNode);
      }
    }
  }
  return regenCounts;
}

map<Node*,boost::shared_ptr<LKernel> > loadKernels(ConcreteTrace * trace,
                                            set<Node*> & drg,
                                            set<Node*> & aaa,
                                            bool useDeltaKernels)
{ 
  map<Node*,boost::shared_ptr<LKernel> > lkernels;
  for (set<Node*>::iterator aaaIter = aaa.begin(); aaaIter != aaa.end(); ++aaaIter)
  {
    OutputNode * outputNode = dynamic_cast<OutputNode*>(*aaaIter);
    assert(outputNode);
    boost::shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(outputNode))->getPSP(outputNode);
    lkernels[*aaaIter] = psp->getAAALKernel();
  }

  if (useDeltaKernels)
    {
      for (set<Node*>::iterator drgIter = drg.begin(); drgIter != drg.end(); ++drgIter)
        {
          OutputNode * outputNode = dynamic_cast<OutputNode*>(*drgIter);
          if (!outputNode) { continue; }
          if (drg.count(outputNode->operatorNode)) { continue; }
          if (aaa.count(outputNode)) { continue; }
          boost::shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(outputNode))->getPSP(outputNode);
          if (psp->hasDeltaKernel()) { lkernels[outputNode] = psp->getDeltaKernel(); }
        }
    }
  return lkernels;
}


vector<vector<Node *> > assignBorderSequnce(set<Node*> & border,
                                            map<Node*,int> & indexAssignments,
                                            int numIndices) 
{
  vector<vector<Node *> > borderSequence(numIndices);
  for (set<Node*>::iterator borderIter = border.begin(); borderIter != border.end(); ++borderIter)
  {
    borderSequence[indexAssignments[*borderIter]].push_back(*borderIter);
  }
  return borderSequence;
}
