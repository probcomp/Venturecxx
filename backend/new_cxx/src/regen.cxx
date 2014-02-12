double regenAndAttach(Trace * trace,
		      const vector<Node*> & border,
		      shared_ptr<Scaffold> scaffold,
		      bool shouldRestore,
		      shared_ptr<DB> db,
		      shared_ptr<map<Node*,Gradient> > gradients)
{
  double weight = 0;
  map<Node*,VentureValuePtr> constraintsToPropagate;
  for (size_t i = 0; i < border.size(); ++i)
  {
    Node * node = border[i];
    if scaffold->isAbsorbing(node) { weight += attach(trace,node,scaffold,shouldRestore,db,gradients); }
    else
    {
      weight += regen(trace,node,scaffold,shouldRestore,db,gradients);
      if (trace->isObservation(node))
      {
        OutputNode * outputNode = trace->getOutermostNonReferenceApplication(node);
	weight += constrain(trace,outputNode,trace->getObservedValue(node));
	constraintsToPropagate[outputNode] = trace->getObservedValue(node);
      }
    }
  }
  for (map<Node*,VentureValuePtr>::iterator iter = constraintsToPropagate.begin();
       iter != constraintsToPropagate.end();
       ++iter)
  {
    Node * node = iter->first;
    for (size_t j = 0; j < trace->getChildren(node).size(); ++j)
    {
      Node * child = trace->getChildren(node)[j];
      propagateConstraint(trace,child,iter->second);
    }
  }
  return weight;
}


double constrain(Trace * trace,
		 Node * node,
		 VentureValuePtr value)
{ throw 500; }



void propagateConstraint(Trace * trace,
			 Node * node,
			 VentureValuePtr value)
{ throw 500; }

double attach(Trace * trace,
	      Node * node,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{ throw 500; }

double regen(Trace * trace,
	      Node * node,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{ 
  if (!scaffold) { return 0; }
  return throw 500; 
}

double regenParents(Trace * trace,
	      Node * node,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{ throw 500; }

double regenESRParents(Trace * trace,
	      Node * node,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{ throw 500; }

pair<double,Node*> evalFamily(Trace * trace,
			      VentureValuePtr exp,
			      shared_ptr<VentureEnvironment> env,
			      shared_ptr<Scaffold> scaffold,
			      bool shouldRestore,
			      shared_ptr<DB> db,
			      shared_ptr<map<Node*,Gradient> > gradients)
{
  if (isVariable(exp))
  {
    Node * sourceNode = env->lookupSymbol(exp);
    weight = regen(trace,sourceNode,scaffold,false,db,gradients);
    return make_pair(weight,trace->createLookupNode(sourceNode));
  }
  else if (isSelfEvaluating(exp)) { return make_pair(0,trace->createConstantNode(exp)); }
  else if (isQuotation(exp)) { return make_pair(0,trace->createConstantNode(textOfQuotation(exp))); }
  else
  {
    pair<double,Node*> p = evalFamily(trace,exp[0],env,scaffold,db,gradients);
    double weight = p.first;
    Node * operatorNode = p.second;
    vector<Node*> operandNodes;
    for (size_t i = 1; i < exp.size(); ++i)
    {
      pair<double,Node*> p = evalFamily(trace,exp[i],env,scaffold,db,gradients);
      weight += p.first;
      operandNodes.push_back(p.second);
    }

    pair<RequestNode*,OutputNode*> p = trace->createApplicationNodes(operatorNode,operandNodes,env);
    weight += apply(trace,p.first,p.second,scaffold,false,db,gradients);
    return make_pair(weight,p.second);
  }
}

double apply(Trace * trace,
	      RequestNode * requestNode,
	     OutputNode * outputNode,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{
  double weight = applyPSP(trace,requestNode,scaffold,shouldRestore,db,gradients);
  weight += evalRequests(trace,requestNode,scaffold,shouldRestore,db,gradients);

  /* DEBUG */
  pair<vector<ESR>,vector<LSR *> > p = trace->getValue(requestNode)->getRequests();
  assert(trace->getESRParents(outputNode).size() == p.first.size());  
  /* END DEBUG */

  weight += regenESRParents(trace,outputNode,scaffold,shouldRestore,db,gradients);
  weight += applyPSP(trace,outputNode,scaffold,shouldRestore,db,gradients);
  return weight;
}



void processMadeSP(Trace * trace, Node * makerNode, bool isAAA)
{
  shared_ptr<VentureSP> sp = dynamic_pointer_cast<VentureSP>(trace->getValue(makerNode));
  if (!isAAA)
  {
    trace->initMadeSPRecord(sp,sp->constructSPAux());
    if (sp->hasAEKernel()) { trace->registerAEKernel(makerNode); }
  }
  else { trace->setMadeSP(makerNode,sp); }
  trace->setValue(node,new VentureSPRef(makerNode));
}

double applyPSP(Trace * trace,
	      Node * node,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{
  double weight = 0;
  shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP();
  shared_ptr<Args> args = trace->getArgs(node);

  VentureValuePtr oldValue;
  VentureValuePtr newValue;

  if (db->hasValueFor(node)) { oldValue = omegaDB.getValue(node); }

  if (scaffold->hasLKernel(node))
  {
    shared_ptr<LKernel> k = scaffold->getLKernel(node);
    if (shouldRestore) { newValue = oldValue; }
    else { newValue = k->simulate(trace,oldValue,args); }

    weight += k->weight(trace,newValue,oldValue,args);
    //TODO variational
  }
  else
  {
    if (shouldRestore) { newValue = oldValue; }
    else { newValue = psp->simulate(args); } // TODO rng
  }

  trace->setValue(node,newValue);
  psp->incorporate(newValue,args);

  if (dynamic_pointer_cast<VentureSP>(newValue)) { processMadeSP(trace,node,scaffold->isAAA(node)); }
  /* TODO TEMP MILESTONE */
  // if (psp->isRandom()) { trace->registerRandomChoice(node); } 
  // if (dynamic_pointer_cast<ScopeIncludeOutputPSP>(psp))
  // {
  //   ScopeID scope = trace->getValue(node->operandNodes[0]);
  //   BlockID block = trace->getValue(node->operandNodes[1]);
  //   Node * blockNode = node->operandNodes[2];
  //   trace->registerRandomChoiceInScope(scope,block,blockNode);
  // }
  return weight;
}


double evalRequests(Trace * trace,
	      RequestNode * requestNode,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{
  weight = 0;
  pair<vector<ESR>,vector<LSR *> > requests = trace->getValue(requestNode)->getRequests();

  for (size_t i = 0; i < requests.first.size(); ++i)
  {
    ESR esr = requests.first[i];
    if (!trace->containsSPFamilyAt(requestNode,esr.id))
    {
      Node * esrParent;
      if (shouldRestore)
      {
        esrParent = db->getESRParent(trace->getMadeSP(trace->getOperatorSPMakerNode(node)),esr.id);
        weight += restore(trace,esrParent,scaffold,db,gradients);
      }
      else
      {
	pair<double,Node*> p = evalFamily(trace,esr.exp,esr.env,scaffold,db,gradients);
        weight += p.first;
	esrParent = p.second;
      }
      trace->registerFamilyAt(node,esr.id,esrParent);
    }
    Node * esrParent = trace->getMadeSPFamilyRoot(trace->getOperatorSPMakerNode(requestNode),esr.id);
    trace.addESREdge(esrParent,requestNode->outputNode);
  }

  // TODO LSRs
  return weight;
}


double restore(Trace * trace,
	      RequestNode * requestNode,
	      shared_ptr<Scaffold> scaffold,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{ throw 500; }
