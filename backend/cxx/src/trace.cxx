ConstantNode * Trace::createConstantNode(VentureValuePtr value) { return ConstantNode(value); }
LookupNode * Trace::createLookupNode(Node * sourceNode)
{
  LookupNode * lookupNode = LookupNode(sourceNode);
  setValueAt(lookupNode,getValue(sourceNode));
  addChildAt(sourceNode,lookupNode);
  return lookupNode;
}


pair<RequestNode*,OutputNode*> Trace::createApplicationNodes(Node *operatorNode,const vector<Node*> & operandNodes,VentureEnvironmentPtr env)
{
/* The Python: */
    // requestNode = RequestNode(operatorNode,operandNodes,env)
    // outputNode = OutputNode(operatorNode,operandNodes,requestNode,env)
    // self.addChildAt(operatorNode,requestNode)
    // self.addChildAt(operatorNode,outputNode)
    // for operandNode in operandNodes:
    //   self.addChildAt(operandNode,requestNode)
    //   self.addChildAt(operandNode,outputNode)
    // requestNode.registerOutputNode(outputNode)
    // return (requestNode,outputNode)
  throw 500;
}


VentureValuePtr getGroundValue(Node * node) { throw 500; }
Node * getSPMakerNode(Node * node) { throw 500; }
shared_ptr<SPRef> getSPRef(Node * node) { throw 500; }
shared_ptr<VentureSP> getSP(Node * node) { throw 500; }
shared_ptr<SPFamilies> getSPFamilies(Node * node) { throw 500; }
shared_ptr<SPAux> getSPAux(Node * node) { throw 500; }
shared_ptr<PSP> getPSP(Node * node) { throw 500; }
vector<Node*> getParents(Node * node) { throw 500; }
