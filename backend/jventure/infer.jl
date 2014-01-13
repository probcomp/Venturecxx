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

####### (2) Enumerative Gibbs
getCurrentValues(trace::Trace,pnodes::Set{Node}) = [getValue(trace,pnode) for pnode in pnodes]
function registerDeterministicLKernels(scaffold::Scaffold,pnodes::Set{Node},currentValues)
  for (pnode,currentValue) = zip(pnodes,currentValues)
    scaffold.lkernels[pnode] = DeterministicLKernel(currentValue) # TODO this must take the PSP as well
  end
end

function getCartesianProductOfEnumeratedValues(trace::Trace,pnodes::Set{Node})
  @assert length(pnodes) <= 2

  allValues = [Set for i in 1:length(pnodes)]
  i = 1
  for pnode = pnodes
    psp = getPSP(trace,pnode)
    
  z = Array(Any,length(x) * length(y))
  for i = 1:length(x)
    for j = 1:length(y)
      k = (j-1) * length(x) + i
      z[k] = (x[i],y[j])
    end
  end
  return z
end



end

function enumerativeGibbsInfer(trace::Trace,scope,block,pnodes::Set{Node})
  @assert length(pnodes) == 1
  assertTrace(trace)
  rhoMix = logDensityofBlock(trace,scope,block)
  scaffold = constructScaffold(trace,pnodes)
  currentValue = getCurrentValue(trace,pnodes)
  registerDeterministicLKernels(scaffold,pnodes,currentValue)
  
  (rhoWeight,rhoDB) = detachAndExtract(trace,scaffold.border,scaffold)
  assertTorus(scaffold)

  xiWeights = []
  xiDBs = []
  
  allValues = getCartesianProductOfEnumeratedValues(trace,pnodes)
  for newValue = allValues
    if (newValue == currentValue) continue end
    registerDeterministicLKernels(scaffold,pnodes,newValue)
    append!(xiWeights,regenAndAttach(trace,scaffold.border,scaffold,false,DB()))
    append!(xiDBs,detachAndExtract(trace,scaffold.border,scaffold)[1])
  end

  allExpWeights = [exp(w) for w in xiWeights + [rhoWeight]]
  xiExpWeights = expWeights[1:end-1]
  i = Distributions.rand(Distributions.Categorical(normalizeList(xiExpWeights)))
  xiWeight,xiDB = xiWeights[i],xiDBs[i]
  totalExpWeight = sum(allExpWeights)
  weightMinusRho = log(totalExpWeight - expWeights[end])
  weightMinusXi = log(totalExpWeight - expWeights[i])
  xiMix = logDensityofBlock(trace,scope,block)

  if log(rand()) < (xiMix + xiWeight) - (rhoMix + rhoWeight) # accept
    regenAndAttach(trace,scaffold.border,scaffold,true,xiDBs[i])
  else # reject
    regenAndAttach(trace,scaffold.border,scaffold,true,rhoDB)
  end
  assertTrace(trace)
end
