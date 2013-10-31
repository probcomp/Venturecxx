#ifndef SCAFFOLD_H
#define SCAFFOLD_H

#include <set>
#include <map>
#include <queue>

#include "node.h"
#include "lkernel.h"

class Scaffold
{

public:
  struct DRGNode
  {
    DRGNode() { assert(false); }
    DRGNode(bool isAAA): isAAA(isAAA) {}

    int regenCount{0};
    bool isAAA;
  };


/* Fake scaffold. */
  Scaffold() {}

/* Constructs real scaffold. */
  Scaffold(std::set<Node *> principalNodes);


/* TODO Most of this should be private. */
  std::map<Node *, DRGNode> drg{};
  std::set<Node *> absorbing{};

  std::map<Node *, LKernel *> lkernels{};
  std::set<Node *> brush{};

  std::vector<Node *> border;

  bool hasAAANodes{false};

  bool isResampling(Node * node) { return drg.count(node); }
  bool isAAA(Node * node) { return isResampling(node) && drg[node].isAAA; }
  bool isAbsorbing(Node * node) { return absorbing.count(node); }
  bool hasKernelFor(Node * node) { return lkernels.count(node); }

  bool csrReferenceCanAbsorb(Node * node)
    {
      return 
	node->nodeType == NodeType::OUTPUT &&
	node->sp->isCSRReference &&
	!isResampling(node->requestNode) &&
	!isResampling(node->csrParents[0]);
    }


/* Removes from A or D if necessary, and adds to the brush. */
  void registerBrush(Node * node) 
    { absorbing.erase(node); drg.erase(node); brush.insert(node); }

  void addResamplingNode(std::queue<std::pair<Node *,bool>> &q, Node * node);
  void addAAANode(Node * node) { drg.emplace(node,true); hasAAANodes = true; }
  void addAbsorbingNode(Node * node) { absorbing.insert(node); }

  bool operatorCannotChange(Node * node) 
    { return !isResampling(node->operatorNode); }
   
  void loadDefaultKernels(bool deltaKernels);

private:

  void assembleERG(std::set<Node *> principalNodes);

  void disableBrush();
  void disableRequests(Node * node, 
		       std::unordered_map<Node *,uint32_t> & disableCounts);
  void disableEval(Node * node,     
		   std::unordered_map<Node *,uint32_t> & disableCounts);


  bool hasChildInAorD(Node * node);
  void processParentsAAA(Node * node);
  void processParentAAA(Node * parent);
  void setRegenCounts();


  
};

std::ostream& operator<<(std::ostream& os, Scaffold * scaffold);

#endif
