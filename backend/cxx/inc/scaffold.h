#ifndef SCAFFOLD_H
#define SCAFFOLD_H

#include <set>
#include <map>
#include <unordered_map>
#include <queue>

#include <cassert>

using namespace std;

struct Node;
struct LKernel;

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
  Scaffold(set<Node *> principalNodes);

  ~Scaffold();

/* TODO Most of this should be private. */
  map<Node *, DRGNode> drg{};
  set<Node *> absorbing{};

  map<Node *, LKernel*> lkernels{};
  set<Node *> brush{};

  vector<Node *> border;

  bool hasAAANodes{false};

  bool isResampling(Node * node) { return drg.count(node); }
  bool isAAA(Node * node) { return isResampling(node) && drg[node].isAAA; }
  bool isAbsorbing(Node * node) { return absorbing.count(node); }
  bool hasKernelFor(Node * node) { return lkernels.count(node); }

  inline bool esrReferenceCanAbsorb(Node * node);

/* Removes from A or D if necessary, and adds to the brush. */
  void registerBrush(Node * node) 
    { absorbing.erase(node); drg.erase(node); brush.insert(node); }

  void addResamplingNode(queue<pair<Node *,bool>> &q, Node * node);
  void addAAANode(Node * node) { drg.emplace(node,true); hasAAANodes = true; }
  void addAbsorbingNode(Node * node) { absorbing.insert(node); }

  void loadDefaultKernels(bool deltaKernels);

private:

  void assembleERG(set<Node *> principalNodes);

  void disableBrush();
  void disableRequests(Node * node, 
		       unordered_map<Node *,uint32_t> & disableCounts);
  void disableEval(Node * node,     
		   unordered_map<Node *,uint32_t> & disableCounts);


  bool hasChildInAorD(Node * node);
  void processParentsAAA(Node * node);
  void processParentAAA(Node * parent);
  void setRegenCounts();

  
};

ostream& operator<<(ostream& os, Scaffold * scaffold);

#endif
