require("psp.jl")

type SP
  requestPSP::RequestPSP
  outputPSP::OutputPSP
  name::String
end

type SPRef
  makerNode::Union(ConstantNode,OutputNode)
end

type SPRecord
  sp::Union(SP,Nothing)
  aux::Any
  families::Dict{SPFamilyID,Node}
end



  # def constructLatentDB(self): return None
  # def simulateLatents(self,spaux,lsr,shouldRestore,latentDB): pass
  # def detachLatents(self,spaux,lsr,latentDB): pass
  # def hasAEKernel(self): return False