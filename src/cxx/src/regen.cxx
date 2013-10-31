#include "node.h"
#include "value.h"
#include "value_types.h"
#include "sp.h"
#include "trace.h"
#include "sps/csp.h"
#include "scaffold.h"
#include "omegadb.h"
#include "srs.h"

#include <iostream>

double Trace::regen(const std::vector<Node *> & border,
		    Scaffold * scaffold,
		    bool shouldRestore,
		    OmegaDB & omegaDB)
{
  double weight = 0;
  for (Node * node : border)
  {
    if (scaffold->isAbsorbing(node)) { weight += absorb(node,scaffold,shouldRestore,omegaDB); }
    else /* Terminal resampling */
    {
      weight += regenInternal(node,scaffold,shouldRestore,omegaDB);
      if (node->isObservation()) { weight += constrain(node,node->observedValue); }
    }
  }
  return weight;
}

/* Note: could be simplified by storing (or quickly computing) the direct parents. */
/* OPT: Since we never have a requestNode in a DRG without its outputNode, we ought
   to be able to only regen the operator and operands once. 
   (This may yield a substantial performance improvement.) */
double Trace::regenParents(Node * node,
			   Scaffold * scaffold,
			   bool shouldRestore,
			   OmegaDB & omegaDB)
{
  assert(node->nodeType != NodeType::VALUE);
  assert(node->nodeType != NodeType::FAMILY_ENV);

  if (node->nodeType == NodeType::LOOKUP)
  { return regenInternal(node->lookedUpNode,scaffold,shouldRestore,omegaDB); }

  double weight = 0;

  weight += regenInternal(node->operatorNode,scaffold,shouldRestore,omegaDB);
  for (Node * operandNode : node->operandNodes)
  { weight += regenInternal(operandNode,scaffold,shouldRestore,omegaDB); }
  
  if (node->nodeType == NodeType::OUTPUT)
  {
    weight += regenInternal(node->requestNode,scaffold,shouldRestore,omegaDB);
    for (Node * csrParent : node->csrParents)
    { weight += regenInternal(csrParent,scaffold,shouldRestore,omegaDB); }
  }
   
  return weight;
}


double Trace::absorb(Node * node,
		     Scaffold * scaffold,
		     bool shouldRestore,
		     OmegaDB & omegaDB)
{
  double weight = 0;
  weight += regenParents(node,scaffold,shouldRestore,omegaDB);
  weight += node->sp->logDensity(node->getValue(),node);
  return weight;
}

double Trace::constrain(Node * node, VentureValue * value)
{
  assert(node->isActive);
  if (node->isReference()) { return constrain(node->sourceNode,value); }
  else
  {
    /* New restriction, to ensure that we did not propose to an
       observation node with a non-trivial kernel. TODO handle
       this in loadDefaultKernels instead. */
    assert(node->sp->isRandomOutput);
    assert(node->sp->canAbsorbOutput); // TODO temporary
    node->sp->removeOutput(node->getValue(),node);
    double weight = node->sp->logDensityOutput(value,node);
    node->setValue(value);
    node->isConstrained = true;
    node->sp->incorporateOutput(value,node);
    if (node->sp->isRandomOutput) { unregisterRandomChoice(node); }
    return weight;
  }
}


/* Note: no longer calls regen parents on REQUEST nodes. */
double Trace::regenInternal(Node * node,
			    Scaffold * scaffold,
			    bool shouldRestore,
			    OmegaDB & omegaDB)
{
  if (!scaffold) { return 0; }
  double weight = 0;

  if (scaffold->isResampling(node))
  {
    Scaffold::DRGNode &drgNode = scaffold->drg[node];
    if (drgNode.regenCount == 0)
    {
      weight += regenParents(node,scaffold,shouldRestore,omegaDB);
      if (node->nodeType == NodeType::LOOKUP)
      { node->registerReference(node->lookedUpNode); }
      else /* Application node */
      { weight += applyPSP(node,scaffold,shouldRestore,omegaDB); }
    }
    drgNode.regenCount++;
  }
  else if (scaffold->hasAAANodes)
  {
    if (node->isReference() && scaffold->isAAA(node->sourceNode))
    { weight += regenInternal(node->sourceNode,scaffold,shouldRestore,omegaDB); }
  }
  return weight;
}

double Trace::applyPSP(Node * node,
		       Scaffold * scaffold,
		       bool shouldRestore,
		       OmegaDB & omegaDB)
{
  SP * sp = node->sp;

  /* Almost nothing needs to be done if this node is a CSRReference.*/
  if (node->nodeType == NodeType::OUTPUT && sp->isCSRReference)
  {
    assert(!node->csrParents.empty());
    node->registerReference(node->csrParents[0]);
    node->isActive = true;
    return 0;
  }

  /* Otherwise we need to actually do things. */

  double weight = 0;

  VentureValue * oldValue = nullptr;
  if (!omegaDB.rcs.empty()) { oldValue = omegaDB.rcs[node->address]; }

  VentureValue * newValue;

  /* Determine new value. */
  if (shouldRestore)
  {
    newValue = oldValue;
    /* If the kernel was an ESR kernel, then we restore all latents.
       TODO this could be made clearer. */
    if (sp->hasLatents() && scaffold->isAAA(node))
    {
      sp->restoreAllLatents(node->spAux,omegaDB.latentDBsbyNode[node]);
    }
  }
  else if (scaffold->hasKernelFor(node))
  {
    LKernel * k = scaffold->lkernels[node];
    /* Awkward. We are not letting the language know about the difference between
       regular LKernels and ESRKernels. We pass a latentDB no matter what, nullptr
       for the former. */
    LatentDB * latentDB = nullptr;
    if (omegaDB.latentDBsbyNode.count(node) == 1) { latentDB = omegaDB.latentDBsbyNode[node]; }
    newValue = k->simulate(oldValue,node,latentDB,rng);
    weight += k->weight(newValue,oldValue,node,latentDB);
  }
  else
  {
    newValue = sp->simulate(node,rng);
  }

  node->setValue(newValue);
  node->isActive = true;

  sp->incorporate(newValue,node);
  if (sp->isRandom(node->nodeType)) { registerRandomChoice(node); }
  if (node->nodeType == NodeType::OUTPUT && sp->hasAEKernel) { registerAEKernel(node); }
  if (node->nodeType == NodeType::REQUEST) { evalRequests(node,scaffold,shouldRestore,omegaDB); }
  
  return weight;
}

double Trace::evalRequests(Node * node,
			   Scaffold * scaffold,
			   bool shouldRestore,
			   OmegaDB & omegaDB)
{
  double weight = 0;
  VentureRequest * requests = dynamic_cast<VentureRequest *>(node->getValue());

  /* First evaluate CSRs. */
  for (CSR csr : requests->csrs)
  {
    Address csrAddr = Address::makeCSRAddress(node->sp->address,csr.name);
    if (!containsAddr(csrAddr)) 
    {
      weight += evalFamily(csrAddr,csr.exp,csr.env,scaffold,shouldRestore,omegaDB);
    }
    /* OPT this lookup could be skipped in some cases. */
    Node::addCSREdge(_map[csrAddr],node->outputNode);
  }

  /* Next evaluate ESRs. */
  for (ESR * esr : requests->esrs)
  {
    LatentDB * latentDB = nullptr;
    if (omegaDB.latentDBsbySP.count(node->sp)) { latentDB = omegaDB.latentDBsbySP[node->sp]; }
    assert(!shouldRestore || latentDB);
    weight += node->sp->simulateLatents(node->spAux,esr,shouldRestore,latentDB,rng);
  }

  return weight;
}


double Trace::evalFamily(Address addr,
			 Expression & exp,
			 Environment env,
			 Scaffold * scaffold,
			 bool shouldRestore,
			 OmegaDB & omegaDB)
{
  Address familyEnvAddr = addr.getFamilyEnvAddress();
  Node * familyEnvNode = makeNode(familyEnvAddr,NodeType::FAMILY_ENV);
  familyEnvNode->setValue(new VentureEnvironment(env));
  familyEnvNode->isActive = true;
  return eval(addr,exp,familyEnvAddr,scaffold,shouldRestore,omegaDB);
}

double Trace::eval(Address addr, 
		   Expression & exp, 
		   Address familyEnvAddr,
		   Scaffold * scaffold,
		   bool shouldRestore,
		   OmegaDB & omegaDB)
{
  double weight = 0;
  switch (exp.expType)
  {
  case ExpType::VALUE:
  {
    VentureValue * value = exp.value;
    Node * node = makeNode(addr,NodeType::VALUE);
    /* TODO URGENT does this copy-construct the whole value? */
    node->setValue(value);
    node->isActive = true;
    break;
  }
  case ExpType::VARIABLE:
  {
    Node * lookedUpNode = findSymbol(exp.sym,familyEnvAddr);
    assert(lookedUpNode);
    weight += regenInternal(lookedUpNode,scaffold,shouldRestore,omegaDB);
    Node * node = makeNode(addr,NodeType::LOOKUP);
    Node::addLookupEdge(lookedUpNode,node);
    node->registerReference(lookedUpNode);
    node->isActive = true;
    break;
  }
  case ExpType::LAMBDA:
  {
    Node * node = makeNode(addr,NodeType::VALUE);
    node->setValue(new VentureSPValue(new CSP(addr,exp.getIDs(),exp.exps[2],familyEnvAddr)));
    node->isActive = true;
    break;
  }
  case ExpType::APPLICATION:
  {
    weight += eval(addr.getOperatorAddress(),exp.exps[0],familyEnvAddr,scaffold,shouldRestore,omegaDB);
    for (uint8_t i = 1; i < exp.exps.size(); ++i)
    {
      weight += eval(addr.getOperandAddress(i),exp.exps[i],familyEnvAddr,scaffold,shouldRestore,omegaDB);
    }
    Node * requestNode = makeNode(addr.getRequestAddress(),NodeType::REQUEST);
    requestNode->familyEnvAddr = familyEnvAddr;
      
    Node * outputNode = makeNode(addr,NodeType::OUTPUT);
    outputNode->familyEnvAddr = familyEnvAddr;

    addApplicationEdges(requestNode,outputNode,exp.exps.size()-1);
    weight += apply(requestNode,outputNode,scaffold,shouldRestore,omegaDB);
    break;
  }
  }
  return weight;
}

double Trace::apply(Node * requestNode,
		    Node * outputNode,
		    Scaffold * scaffold,
		    bool shouldRestore,
		    OmegaDB & omegaDB)
{
  double weight = 0;

  /* Call the requester PSP. */
  weight += applyPSP(requestNode,scaffold,shouldRestore,omegaDB);
  
  /* Regenerate any CSR nodes requested. */
  VentureRequest * requests = dynamic_cast<VentureRequest *>(requestNode->getValue());
  for (CSR csr : requests->csrs)
  {
    Address csrAddr = Address::makeCSRAddress(requestNode->sp->address,csr.name);
    Node * csrNode = _map[csrAddr];
    weight += regenInternal(csrNode,scaffold,shouldRestore,omegaDB);
  }
  
  /* Call the output PSP. */
  weight += applyPSP(outputNode,scaffold,shouldRestore,omegaDB);
  return weight;
}
