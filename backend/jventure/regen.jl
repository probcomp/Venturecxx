require("exp.jl")

function regenAndAttach(trace::Trace,border::Array{Node},scaffold::Scaffold,shouldRestore::Bool,db::DB)
  weight = 0.0
  for node = border
    if isAbsorbing(scaffold,node)
      weight += attach(trace,node,scaffold,shouldRestore,db)
    else
      weight += regen(trace,node,scaffold,shouldRestore,db)
      if isObservation(trace,node)
        weight += constrain(trace,node,getObservedValue(trace,node))
      end
    end
  end
  return weight
end

constrain(trace::Trace,node::LookupNode,value::Any) = constrain(trace,node.sourceNode,value)
function constrain(trace::Trace,node::Node,value::Any)
  if isa(getPSP(trace,node),ESRRefOutputPSP)
    return constrain(trace,getESRSourceNode(trace,node),value)
  else
    (psp,args) = (getPSP(trace,node),getArgs(trace,node))
    oldValue = getGroundValue(trace,node)
    unincorporate!(psp,oldValue,args)
    weight = logDensity(psp,value,args)
    setValue!(trace,node,value)
    incorporate!(psp,value,args)
    setConstrained!(trace,node)
    unregisterRandomChoice!(trace,node)
    return weight
  end
end

function attach(trace::Trace,node::ApplicationNode,scaffold::Scaffold,shouldRestore::Bool,db::DB)
  weight = regenParents(trace,node,scaffold,shouldRestore,db)
  (psp::PSP,args::Args,value) = (getPSP(trace,node),getArgs(trace,node),getGroundValue(trace,node))
  weight += logDensity(psp,value,args)
  incorporate!(psp,value,args)
  return weight
end

function regenParents(trace::Trace,node::Node,scaffold::Scaffold,shouldRestore::Bool,db::DB)
  weight = 0.0
  for parent = getParents(trace,node)
    weight += regen(trace,parent,scaffold,shouldRestore,db)
  end
  return weight
end

function regen(trace::Trace,node::Node,scaffold::Scaffold,shouldRestore::Bool,db::DB)
  weight = 0.0
  if isResampling(scaffold,node)
    if getRegenCount(scaffold,node) == 0
      weight += regenParents(trace,node,scaffold,shouldRestore,db)
      if isa(node,LookupNode)
        setValue!(trace,node,getValue(trace,node.sourceNode))
      else
        weight += applyPSP(trace,node,scaffold,shouldRestore,db)
        if isa(node,RequestNode)
          weight += evalRequests(trace,node,scaffold,shouldRestore,db)
        end
      end
    end
    incrementRegenCount!(scaffold,node)
  end

  value = getValue(trace,node)
  if isa(value,SPRef) && value.makerNode != node && isAAA(scaffold,value.makerNode)
    weight += regen(trace,value.makerNode,scaffold,shouldRestore,db)
  end

  return weight
end


function evalFamily(trace::Trace,sym::Symbol,env::ExtendedEnvironment,scaffold::Scaffold,db::DB)
  sourceNode = findSymbol(env,sym)
  regen(trace,sourceNode,scaffold,false,db)
  return (0,createLookupNode(trace,sourceNode))
end

function evalFamily(trace::Trace,value::VentureValue,env::ExtendedEnvironment,scaffold::Scaffold,db::DB)
  return (0,createConstantNode(trace,value))
end

function evalFamily(trace::Trace,exp::Array{VentureValue},env::ExtendedEnvironment,scaffold::Scaffold,db::DB)
  @assert !isempty(exp)
  if isQuotation(exp)
    return (0,createConstantNode(trace,textOfQuotation(exp)))
  else
    (weight::Float64,operatorNode::Node) = evalFamily(trace,getOperator(exp),env,scaffold,db)
    operands = getOperands(exp)
    operandNodes = Array(Node,length(operands))
    for i in 1:length(operands)
      (w::Float64,operandNodes[i]) = evalFamily(trace,operands[i],env,scaffold,db)
      weight += w
    end

    (requestNode,outputNode) = createApplicationNodes(trace,operatorNode,operandNodes,env)
    weight += apply(trace,requestNode,outputNode,scaffold,false,db)
    return weight,outputNode
  end
end

function apply(trace::Trace,requestNode::RequestNode,outputNode::OutputNode,scaffold::Scaffold,shouldRestore::Bool,db::DB)
  weight = applyPSP(trace,requestNode,scaffold,shouldRestore,db)
  weight += evalRequests(trace,requestNode,scaffold,shouldRestore,db)
  weight += applyPSP(trace,outputNode,scaffold,shouldRestore,db)
  return weight
end

function processMadeSP(trace::Trace,node::Union(ConstantNode,OutputNode),isAAA::Bool)
  sp = getValue(trace,node)
  @assert isa(sp,SP)
  if !isAAA
    createMadeSPRecord!(trace,node,sp,constructSPAux(sp.outputPSP))
    if hasAEKernel(sp.outputPSP) registerAEKernel!(trace,node) end
  else
    setMadeSP!(trace,node,sp)
  end
  setValue!(trace,node,SPRef(node))
end

function applyPSP(trace::Trace,node::ApplicationNode,scaffold::Scaffold,shouldRestore::Bool,db::DB)
  (psp,args) = (getPSP(trace,node),getArgs(trace,node))
  weight = 0.0

  if hasValue(db,node)
    oldValue = getValue(db,node)
  else
    oldValue = nothing
  end

  if shouldRestore
    @assert hasValue(db,node)
    newValue = oldValue
  elseif hasLKernel(scaffold,node)
    k = getLKernel(scaffold,node)
    newValue = ksimulate(k,trace,oldValue,args)
    weight += kweight(k,trace,newValue,oldValue,args)
  else
    newValue = simulate(psp,args)
  end

  @assert newValue != nothing
  setValue!(trace,node,newValue)
  incorporate!(psp,newValue,args)

  @assert !node.valid
  node.valid = true

  if isa(newValue,SP) processMadeSP(trace,node,isAAA(scaffold,node)) end
  if isRandom(psp) registerRandomChoice!(trace,node) end
  if isa(psp,ApplyInScopeOutputPSP)
    operandNodes = getOperandNodes(trace,node)
    (scope,block) = [getValue(trace,n) for n in operandNodes[1:2]]
    blockNode = operandNodes[3]
    @assert isRandom(getPSP(trace,blockNode))
    registerRandomChoiceInScope!(trace,scope,block,blockNode)
  end
  return weight
end

function evalRequests(trace::Trace,node::RequestNode,scaffold::Scaffold,shouldRestore::Bool,db::DB)
  weight = 0.0
  request = getValue(trace,node)

  spRecord = getSPRecord(trace,node)
  (sp,aux,families) = (spRecord.sp,spRecord.aux,spRecord.families)

  # first evaluate exposed simulation requests (ESRs)
  for esr = request.esrs
    if !haskey(families,esr.id)
      if shouldRestore
        esrParent = getSPFamilyRoot(db,sp,esr.id)
        weight += restore(trace,esrParent,scaffold,db)
      else
        (w,esrParent) = evalFamily(trace,esr.exp,esr.env,scaffold,db)
        weight += w
      end
      families[esr.id] = esrParent
    else
      esrParent = families[esr.id]
      weight += regen(trace,esrParent,scaffold,shouldRestore,db)
    end
    esrParent = families[esr.id]
    registerESREdge!(trace,esrParent,getOutputNode(trace,node))
  end
  return weight
end


#TODO

function restore(trace::Trace,node::Node,scaffold::Scaffold,db::DB)
  if isa(node,ConstantNode)
    return 0
  elseif isa(node,LookupNode)
    weight = regen(trace,node.sourceNode,scaffold,true,db)
    setValue!(trace,node,getValue(trace,node.sourceNode))
    reconnectLookup!(trace,node)
    return weight
  else # node is output node
    weight = restore(trace,getOperatorNode(trace,node),scaffold,db)
    for operandNode = getOperandNodes(trace,node)
      weight += restore(trace,operandNode,scaffold,db)
    end
    weight += apply(trace,node.requestNode,node,scaffold,true,db)
    return weight
  end
end