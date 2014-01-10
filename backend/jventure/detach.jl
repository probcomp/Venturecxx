function detachAndExtract(trace::Trace,border::Array{Node},scaffold::Scaffold)
  weight = 0.0
  db = DB()
  for node = reverse(border)
    if isAbsorbing(scaffold,node)
      weight += detach(trace,node,scaffold,db)
    else
      if isObservation(trace,node)
        weight += unconstrain(trace,node)
      end
      weight += extract(trace,node,scaffold,db)
    end
  end
  return (weight,db)
end

unconstrain(trace::Trace,node::LookupNode) = unconstrain(trace,node.sourceNode)
function unconstrain(trace::Trace,node::OutputNode)
  if isa(getPSP(trace,node),ESRRefOutputPSP)
    return unconstrain(trace,getESRSourceNode(trace,node))
  else
    (psp,args,value) = (getPSP(trace,node),getArgs(trace,node),getValue(trace,node))
    registerRandomChoice!(trace,node)
    setUnconstrained!(trace,node)
    unincorporate!(psp,value,args)
    weight = logDensity(psp,value,args)
    incorporate!(psp,value,args)
    return weight
  end
end

function detach(trace::Trace,node::ApplicationNode,scaffold::Scaffold,db::DB)
  (psp,args,value) = (getPSP(trace,node),getArgs(trace,node),getGroundValue(trace,node))
  unincorporate!(psp,value,args)
  weight = logDensity(psp,value,args)
  weight += extractParents(trace,node,scaffold,db)
  return weight
end

function extractParents(trace::Trace,node::Node,scaffold::Scaffold,db::DB)
  weight = 0.0
  for parent = reverse(getParents(trace,node))
    weight += extract(trace,parent,scaffold,db)
  end
  return weight
end

function extract(trace::Trace,node::Node,scaffold::Scaffold,db::DB)
  weight = 0.0

  value = getValue(trace,node)
  if isa(value,SPRef) && value.makerNode != node && isAAA(scaffold,value.makerNode)
    weight += extract(trace,value.makerNode,scaffold,db)
  end

  if isResampling(scaffold,node)
    decrementRegenCount!(scaffold,node)
    @assert getRegenCount(scaffold,node) >= 0
    if getRegenCount(scaffold,node) == 0
      if isa(node,ApplicationNode)
        if isa(node,RequestNode) 
          weight += unevalRequests(trace,node,scaffold,db)
        end
        weight += unapplyPSP(trace,node,scaffold,db)
      end
      weight += extractParents(trace,node,scaffold,db)
    end
  end
  return weight
end

function unevalFamily(trace::Trace,node::Node,scaffold::Scaffold,db::DB)
  weight = 0.0
  if isa(node,ConstantNode)
    nothing
  elseif isa(node,LookupNode)
    disconnectLookup!(trace,node)
    weight += extract(trace,node.sourceNode,scaffold,db)
  else
    @assert isa(node,OutputNode)
    weight += unapply(trace,node,scaffold,db)
    for operandNode = reverse(getOperandNodes(trace,node))
      weight += unevalFamily(trace,operandNode,scaffold,db)
    end
    weight += unevalFamily(trace,getOperatorNode(trace,node),scaffold,db)
  end
  return weight
end

function unapply(trace::Trace,node::OutputNode,scaffold::Scaffold,db::DB)
  weight = unapplyPSP(trace,node,scaffold,db)
  weight += unevalRequests(trace,node.requestNode,scaffold,db)
  weight += unapplyPSP(trace,node.requestNode,scaffold,db)
  return weight
end

function teardownMadeSP(trace::Trace,node::Union(ConstantNode,OutputNode),isAAA::Bool)
  sp = getMadeSP(trace,node)
  setValue!(trace,node,sp)
  if !isAAA
    if hasAEKernel(sp.outputPSP) unregisterAEKernel!(trace,node) end
    destroyMadeSPRecord!(trace,node)
  else
    setMadeSP!(trace,node,nothing)
  end
end

function unapplyPSP(trace::Trace,node::ApplicationNode,scaffold::Scaffold,db::DB)

  (psp,args) = (getPSP(trace,node),getArgs(trace,node))

  if isRandom(psp) unregisterRandomChoice!(trace,node) end
  if isa(getValue(trace,node),SPRef) && getValue(trace,node).makerNode == node
    teardownMadeSP(trace,node,isAAA(scaffold,node))
  end

  weight = 0.0

  @assert node.valid
  node.valid = false

  unincorporate!(psp,getValue(trace,node),args)
  if hasLKernel(scaffold,node)
    weight += kreverseWeight(getLKernel(scaffold,node),trace,getValue(trace,node),args)
  end
  extractValue(db,node,getValue(trace,node))
  setValue!(trace,node,nothing)
  return weight
end

function unevalRequests(trace::Trace,node::RequestNode,scaffold::Scaffold,db::DB)
  weight = 0.0
  request = getValue(trace,node)

  spRecord = getSPRecord(trace,node)
  (sp,aux,families) = (spRecord.sp,spRecord.aux,spRecord.families)

  for esr = reverse(request.esrs)
    esrParent = popLastESRParent!(trace,getOutputNode(trace,node))
    if getNumberOfRequests(trace,esrParent) == 0
      # TODO current spot
      delete!(families,esr.id)
      registerSPFamilyRoot!(db,sp,esr.id,esrParent)
      weight += unevalFamily(trace,esrParent,scaffold,db)
    else
      weight += extract(trace,esrParent,scaffold,db)
    end
  end
  return weight
end