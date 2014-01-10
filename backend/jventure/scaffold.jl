require("node.jl")
require("lkernel.jl")

type Scaffold
  regenCounts::Dict{Node,Int}
  absorbing::Set{Node}
  aaa::Set{Node}
  border::Array{Node}
  lkernels::Dict{Node,LKernel}
end

Scaffold() = Scaffold((Node=>Int)[],Set{Node}(),Set{Node}(),Array(Node,0),Dict{Node,LKernel}())

getRegenCount(scaffold::Scaffold,node::Node) = scaffold.regenCounts[node]
incrementRegenCount!(scaffold::Scaffold,node::Node) = scaffold.regenCounts[node] += 1
decrementRegenCount!(scaffold::Scaffold,node::Node) = scaffold.regenCounts[node] -= 1
isResampling(scaffold::Scaffold,node::Node) = haskey(scaffold.regenCounts,node)
isAbsorbing(scaffold::Scaffold,node::Node) = in(node,scaffold.absorbing)
isAAA(scaffold::Scaffold,node::Node) = in(node,scaffold.aaa)
hasLKernel(scaffold::Scaffold,node::Node) = haskey(scaffold.lkernels,node)
getLKernel(scaffold,node) = scaffold.lkernels[node]

function constructScaffold(trace::Trace,pnodes::Set{Node})
  (cDRG,cAbsorbing,cAAA) = findCandidateScaffold(trace,pnodes)
  brush = findBrush(trace,cDRG,cAbsorbing,cAAA)
  drg,absorbing,aaa = removeBrush(cDRG,cAbsorbing,cAAA,brush)
  border = findBorder(trace,drg,absorbing,aaa)
  regenCounts = computeRegenCounts(trace,drg,absorbing,aaa,border,brush)
  lkernels = loadKernels(trace,drg,aaa)
  return Scaffold(regenCounts,absorbing,aaa,(Node)[x for x in border],lkernels)
end

function addResamplingNode(trace::Trace,drg::Set{Node},absorbing::Set{Node},q::Array{(Node,Bool)},node::Node)
  delete!(absorbing,node)
  push!(drg,node)
  for child = getChildren(trace,node)
    push!(q,(child,false))
    if isa(child,RequestNode)
      push!(q,(getOutputNode(trace,child),false))
    end
  end
end

function esrReferenceCanAbsorb(trace::Trace,drg::Set{Node},node::OutputNode)
  return isa(getPSP(trace,node),ESRRefOutputPSP) && !in(node.requestNode,drg) && !in(getESRSourceNode(trace,node),drg)
end

esrReferenceCanAbsorb(trace::Trace,drg::Set{Node},node::Node) = false

function findCandidateScaffold(trace::Trace,pnodes::Set{Node})
  (drg,absorbing,aaa,q) = (Set{Node}(),Set{Node}(),Set{Node}(),Array((Node,Bool),0))
  for pnode = pnodes
    push!(q,(pnode,true))
  end

  while !isempty(q)
    (node,isPrincipal) = pop!(q)
    if in(node,drg)
      continue
    elseif isa(node,LookupNode)
      addResamplingNode(trace,drg,absorbing,q,node)
    elseif in(getOperatorNode(trace,node),drg)
      addResamplingNode(trace,drg,absorbing,q,node)
    elseif canAbsorb(getPSP(trace,node)) && !isPrincipal
      push!(absorbing,node)
    elseif esrReferenceCanAbsorb(trace,drg,node)
      push!(absorbing,node)
    elseif childrenCanAAA(getPSP(trace,node))
      push!(drg,node)
      push!(aaa,node)
    else
      addResamplingNode(trace,drg,absorbing,q,node)
    end
  end
  return (drg,absorbing,aaa)
end
      
function findBrush(trace::Trace,cDRG::Set{Node},cAbsorbing::Set{Node},cAAA::Set{Node})
  disableCounts = Dict{Node,Int}()
  disabledRequests = Set{RequestNode}()
  brush = Set{Node}()
  for node = cDRG
    if isa(node,RequestNode)
      disableRequests(trace,node,disableCounts,disabledRequests,brush)
    end
  end

  return brush
end

function removeBrush(cDRG::Set{Node},cAbsorbing::Set{Node},cAAA::Set{Node},brush::Set{Node})
  return (setdiff(cDRG,brush),setdiff(cAbsorbing,brush),setdiff(cAAA,brush))
end

function disableRequests(trace::Trace,node::RequestNode,disableCounts::Dict{Node,Int},disabledRequests::Set{RequestNode},brush::Set{Node})
  if in(node,disabledRequests)
    return
  end
  for esrParent = getESRParents(trace,getOutputNode(trace,node)) # ERROR access to undefined reference
    if !haskey(disableCounts,esrParent)
      disableCounts[esrParent] = 1
    else
      disableCounts[esrParent] += 1
    end
    if disableCounts[esrParent] == getNumberOfRequests(trace,esrParent)
      disableFamily(trace,esrParent,disableCounts,disabledRequests,brush)
    end
  end
end

function registerBrush!(trace,brush,node)
  push!(brush,node)
end  

function disableFamily(trace::Trace,node::Node,disableCounts::Dict{Node,Int},disabledRequests::Set{RequestNode},brush::Set{Node})
  registerBrush!(trace,brush,node)
  if isa(node,OutputNode)
    registerBrush!(trace,brush,node.requestNode)
    disableRequests(trace,node.requestNode,disableCounts,disabledRequests,brush)
    disableFamily(trace,getOperatorNode(trace,node),disableCounts,disabledRequests,brush)
    for operandNode = getOperandNodes(trace,node)
      disableFamily(trace,operandNode,disableCounts,disabledRequests,brush)
    end
  end
end

function findBorder(trace::Trace,drg::Set{Node},absorbing::Set{Node},aaa::Set{Node})
  border::Set{Node} = union(absorbing,aaa)
  for node::Node = setdiff(drg,aaa)
    if isempty(intersect(getChildren(trace,node),union(drg,absorbing)))
      push!(border,node)
    end
  end
  return border
end

maybeIncrementAAARegenCount(trace::Trace,node::Node,regenCounts::Dict{Node,Int}) = error("Not yet implemented!")

function computeRegenCounts(trace::Trace,drg::Set{Node},absorbing::Set{Node},aaa::Set{Node},border::Set{Node},brush::Set{Node})

  regenCounts = Dict{Node,Int}()
  for node = drg
    if in(node,aaa)
      regenCounts[node] = 1 # will be added to shortly
    elseif in(node,border)
      regenCounts[node] = getNumberOfChildren(trace,node) + 1
    else
      regenCounts[node] = getNumberOfChildren(trace,node)
    end
  end
  
  if !isempty(aaa)
    for node = union(drg,absorbing)
      for parent = getParents(trace,node)
        maybeIncrementAAARegenCount(trace,regenCounts,aaa,parent)
      end
    end
    for node = brush
      if isa(node,OutputNode)
        for esrParent = getESRParents(trace,node)
          maybeIncrementAAARegenCount(trace,regenCounts,aaa,esrParent)
        end
      elseif isa(node,LookupNode)
        maybeIncrementAAARegenCount(trace,regenCounts,aaa,node.sourceNode)
      end
    end
  end
  return regenCounts
end

function maybeIncrementAAARegenCount(trace::Trace,regenCounts::Dict{Node,Int},aaa::Set{Node},node::Node)
  value = getValue(trace,node)
  if isa(value,SPRef) && node != value.makerNode && in(value.makerNode,aaa)
    regenCounts[value.makerNode] += 1
  end
end

loadKernels(trace::Trace,drg::Set{Node},aaa::Set{Node}) = (Node=>LKernel)[node => getAAALKernel(getPSP(trace,node)) for node in aaa]

