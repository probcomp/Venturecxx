from node import OutputNode

class Args():
  def __init__(self,node):
    self.node = node
    self.operandValues = [operandNode.value for operandNode in node.operandNodes]
    self.operandNodes = node.operandNodes

    if isinstance(node,OutputNode): 
      self.requestValue = node.request.value
      self.esrValues = [esrParent.value for esrParent in node.esrParents]
      self.esrParents = node.esrParents
      self.madeSPAux = node.madeSPAux
      self.isOutput = True

    self.spaux = node.spaux()
    self.env = node.env
