require("consistency.jl")
require("detach.jl")

####### (1) MH

function mhInfer(trace::Trace,scope,block,pnodes::Set{Node})
  assertTrace(trace)
  rhoMix = logDensityOfBlock(trace,scope,block)
  scaffold = constructScaffold(trace,pnodes)
  (rhoWeight,rhoDB) = detachAndExtract(trace,scaffold.border,scaffold)
  assertTorus(scaffold)
  xiWeight = regenAndAttach(trace,scaffold.border,scaffold,false,rhoDB)
  assertTrace(trace)
  xiMix = logDensityOfBlock(trace,scope,block)
  if log(rand()) > (xiMix + xiWeight) - (rhoMix + rhoWeight) # reject
    detachAndExtract(trace,scaffold.border,scaffold)
    assertTorus(scaffold)
    regenAndAttach(trace,scaffold.border,scaffold,true,rhoDB)
    assertTrace(trace)
  end
end


unbox(a::Array) = unbox(a[1])
unbox(a) = a

####### (2) Enumerative Gibbs
getCurrentValues(trace::Trace,pnodes::Set{Node}) = [getValue(trace,pnode) for pnode in pnodes]
function registerDeterministicLKernels(trace::Trace,scaffold::Scaffold,pnodes::Set{Node},currentValues)
  for (pnode,currentValue) = zip(pnodes,currentValues)
    # TODO unbox is a hack.
    # this would fail if a stochastic SP that returns arrays can enumerate its values
    scaffold.lkernels[pnode] = DeterministicLKernel(getPSP(trace,pnode),unbox(currentValue)) 
  end
end

function getCartesianProductOfEnumeratedValues(trace::Trace,pnodes::Set{Node})
  @assert !isempty(pnodes)
  enumeratedValues = [[{v} for v in enumerateValues(getPSP(trace,pnode),getArgs(trace,pnode))] for pnode in pnodes]
  @assert !isempty(enumeratedValues)
  return cartesianProduct(enumeratedValues)
end


function enumerativeGibbsInfer(trace::Trace,scope,block,mutating_pnodes::Set{Node})
  pnodes = copy(mutating_pnodes)
  assertTrace(trace)
  rhoMix = logDensityOfBlock(trace,scope,block)
  scaffold = constructScaffold(trace,pnodes)

  currentValues = getCurrentValues(trace,pnodes)
  allSetsOfValues = getCartesianProductOfEnumeratedValues(trace,pnodes)

  # println("All sets of values:")
  # show(allSetsOfValues)
  # println("------------------")

  registerDeterministicLKernels(trace,scaffold,pnodes,currentValues)
  
  (rhoWeight,rhoDB) = detachAndExtract(trace,scaffold.border,scaffold)
  @assert isa(rhoDB,DB)
  assertTorus(scaffold)

  xiWeights = (Float64)[]
  xiDBs = {}
  xiMixs = (Float64)[]
  

  for newValues = allSetsOfValues
    if (newValues == currentValues) continue end

    registerDeterministicLKernels(trace,scaffold,pnodes,newValues)
    push!(xiWeights,regenAndAttach(trace,scaffold.border,scaffold,false,DB()))
    push!(xiMixs,logDensityOfBlock(trace,scope,block))
    push!(xiDBs,detachAndExtract(trace,scaffold.border,scaffold)[2])
  end

  xiExpWeights = [exp(w) for w in xiWeights]
  rhoExpWeight = exp(rhoWeight)

  # println("-----------")
  # println("\nxi:")
  # show(xiExpWeights)
  # println("\nrho:")
  # show(rhoExpWeight)
  # println("-----------")

  i = Distributions.rand(Distributions.Categorical(normalizeList(xiExpWeights)))
  (xiWeight,xiDB,xiMix) = (xiWeights[i],xiDBs[i],xiMixs[i])
  totalExpWeight = sum(xiExpWeights) + rhoExpWeight
  weightMinusRho = log(totalExpWeight - rhoExpWeight)
  weightMinusXi = log(totalExpWeight - xiExpWeights[i])

  if log(rand()) < (xiMix + weightMinusRho) - (rhoMix + weightMinusXi) # accept
    print(".")
    regenAndAttach(trace,scaffold.border,scaffold,true,xiDB)
  else # reject
    print("!")
    regenAndAttach(trace,scaffold.border,scaffold,true,rhoDB)
  end
  assertTrace(trace)
end
