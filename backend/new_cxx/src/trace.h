
  /* Registering metadata */
void Trace::registerAEKernel(Node * node);
  virtual void Trace::registerRandomChoice(Node * node) =0;
  virtual void Trace::registerRandomChoiceInScope(ScopeID scope,BlockID block,Node * node) =0;
  virtual void Trace::registerConstrainedChoice(Node * node) =0;

  /* Unregistering metadata */
  virtual void Trace::unregisterAEKernel(Node * node) =0;
  virtual void Trace::unregisterRandomChoice(Node * node) =0;
  virtual void Trace::unregisterRandomChoiceInScope(ScopeID scope,BlockID block,Node * node) =0;
  virtual void Trace::unregisterConstrainedChoice(Node * node) =0;

  /* Creating nodes */
  ConstantNode * Trace::createConstantNode(VentureValuePtr);
  LookupNode * Trace::createLookupNode(Node * sourceNode);
  pair<RequestNode*,OutputNode*> Trace::createApplicationNodes(Node *operatorNode,const vector<Node*> & operandNodes,VentureEnvironmentPtr env);

  /* Regen mutations */
  void Trace::addESREdge(Node *esrParent,OutputNode * outputNode);
  void Trace::reconnectLookup(LookupNode * lookupNode);
  void Trace::incNumRequests(Node * node);
  void Trace::addChild(Node * node, Node * child);

  /* Detach mutations */  
  Node * Trace::popLastESRParent(OutputNode * outputNode);
  void Trace::disconnectLookup(LookupNode * lookupNode);
  void Trace::decNumRequests(Node * node);
  def Trace::removeChild(Node * node, Node * child);

  /* Primitive getters */
  VentureValuePtr Trace::getValue(Node * node);
  SPRecord Trace::getMadeSPRecord(OutputNode * makerNode);
  vector<Node*> Trace::getESRParents(Node * node);
  set<Node*> Trace::getChildren(Node * node);
  int Trace::getNumRequests(Node * node);
  int Trace::getRegenCount(shared_ptr<Scaffold> scaffold,Node * node);
  VentureValuePtr Trace::getObservedValue(Node * node);

  bool Trace::isConstrained(Node * node);
  bool Trace::isObservation(Node * node);

  /* Derived getters (just for convenience)*/
  VentureValuePtr Trace::getGroundValue(Node * node);
  Node * Trace::getSPMakerNode(Node * node);
  shared_ptr<SPRef> Trace::getSPRef(Node * node);
  shared_ptr<VentureSP> Trace::getSP(Node * node);
  shared_ptr<SPFamilies> Trace::getSPFamilies(Node * node);
  shared_ptr<SPAux> Trace::getSPAux(Node * node);
  shared_ptr<PSP> Trace::getPSP(Node * node);
  vector<Node*> Trace::getParents(Node * node);

  /* Primitive setters */
  void Trace::setValue(Node * node, VentureValuePtr value);
  void Trace::clearValue(Node * node);

  void Trace::createSPRecord(OutputNode * makerNode); // No analogue in VentureLite

  void Trace::initMadeSPFamilies(Node * node);
  void Trace::clearMadeSPFamilies(Node * node);

  void Trace::setMadeSP(Node * node,shared_ptr<VentureSP> sp);
  void Trace::setMadeSPAux(Node * node,shared_ptr<SPAux> spaux);

  void Trace::setChildren(Node * node,set<Node*> children);
  void Trace::setESRParents(Node * node,const vector<Node*> & esrParents);

  void Trace::setNumRequests(Node * node,int num);

  /* SPFamily operations */
  // Note: this are different from current VentureLite, since it does not automatically jump
  // from a node to its spmakerNode. (motivation: avoid confusing non-commutativity in particles)
  void Trace::registerMadeSPFamily(OutputNode * makerNode, FamilyID id, Node * esrParent);
  void Trace::unregisterMadeSPFamily(OutputNode * maderNode, FamilyID id, Node * esrParent);
  bool Trace::containsMadeSPFamily(OutputNode * makerNode, FamilyID id);
  Node * Trace::getMadeSPFamilyRoot(OutputNode * makerNode, FamilyID id);

};

struct ConcreteTrace : Trace
{
  BlockID sampleBlock(ScopeID scope);
  double logDensityOfBlock(ScopeID scope);
  vector<BlockID> blocksInScope(ScopeID scope); // TODO this should be an iterator
  int numBlocksInScope(ScopeID scope);
  set<Node*> getAllNodesInScope(ScopeID scope);
    
  vector<set<Node*> > getOrderedSetsInScope(ScopeID scope);

  // TODO Vlad: read this carefully. The default scope is handled differently than the other scopes.
  // For default, the nodes are the actualy principal nodes.
  // For every other scope, they are only the roots w.r.t. the dynamic scoping rules.
  set<Node*> getNodesInBlock(ScopeID scope, BlockID block);

  // Helper function for dynamic scoping
  void addRandomChoicesInBlock(ScopeID scope, BlockID block,set<Node*> & pnodes,Node * node);

  bool scopeHasEntropy(ScopeID scope); 
  void makeConsistent();
  Node * getOutermostNonRefAppNode(Node * node);

  int numRandomChoices();

  int getSeed();
  double getGlobalLogScore();

  // Helpers for particle commit
  void addNewMadeSPFamilies(Node * node, PMap newMadeSPFamilies);
  void addNewChildren(Node * node,PSet newChildren);

private:
  VentureEnvironment * globalEnvironment;
  set<Node*> unconstrainedRandomChoices;
  set<Node*> constrainedChoices;
  set<Node*> arbitraryErgodicKernels;
  set<Node*> unpropagatedObservations;
  map<DirectiveID,RootNodePtr> families;
  map<ScopeID,SMap<BlockID,set<Node*> > scopes;

  map<Node*, vector<Node*> > esrParents;
  map<Node*, int> numRequests;
  map<Node*, SPRecord> madeSPRecords;
  map<Node*,set<Node*> > children;
  map<Node*,VentureValuePtr> observedValues;


};

#endif
