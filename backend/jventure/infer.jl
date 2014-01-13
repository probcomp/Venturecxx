require("consistency.jl")
require("detach.jl")

####### (1) MH

function mhInfer(trace::Trace,scope,block,mutatingPNodes::Set{Node})
  pnodes = copy(mutatingPNodes)
  assertTrace(trace)
  rhoMix = logDensityOfBlock(trace,scope,block)
  scaffold = constructScaffold(trace,{pnodes})
  (rhoWeight,rhoDB) = detachAndExtract(trace,scaffold.border[1],scaffold)
  assertTorus(scaffold)
  xiWeight = regenAndAttach(trace,scaffold.border[1],scaffold,false,rhoDB)
  assertTrace(trace)
  xiMix = logDensityOfBlock(trace,scope,block)
  if log(rand()) > (xiMix + xiWeight) - (rhoMix + rhoWeight) # reject
    detachAndExtract(trace,scaffold.border[1],scaffold)
    assertTorus(scaffold)
    regenAndAttach(trace,scaffold.border[1],scaffold,true,rhoDB)
    assertTrace(trace)
  end
end



####### (2) Enumerative Gibbs

unbox(a::Array) = unbox(a[1])
unbox(a) = a

getCurrentValues(trace::Trace,pnodes::Set{Node}) = [getValue(trace,pnode) for pnode in pnodes]
function registerDeterministicLKernels(trace::Trace,scaffold::Scaffold,pnodes::Set{Node},currentValues)
  for (pnode,currentValue) = zip(pnodes,currentValues)
    # TODO unbox is a hack.
    # FIXME this would fail if a stochastic SP that returns arrays can enumerate its values
    scaffold.lkernels[pnode] = DeterministicLKernel(getPSP(trace,pnode),unbox(currentValue)) 
  end
end

function getCartesianProductOfEnumeratedValues(trace::Trace,pnodes::Set{Node})
  @assert !isempty(pnodes)
  enumeratedValues = [[{v} for v in enumerateValues(getPSP(trace,pnode),getArgs(trace,pnode))] for pnode in pnodes]
  @assert !isempty(enumeratedValues)
  return cartesianProduct(enumeratedValues)
end


function enumerativeGibbsInfer(trace::Trace,scope,block,mutatingPNodes::Set{Node})
  pnodes = copy(mutatingPNodes)
  assertTrace(trace)
  rhoMix = logDensityOfBlock(trace,scope,block)
  scaffold = constructScaffold(trace,{pnodes})

  currentValues = getCurrentValues(trace,pnodes)
  allSetsOfValues = getCartesianProductOfEnumeratedValues(trace,pnodes)

  registerDeterministicLKernels(trace,scaffold,pnodes,currentValues)
  
  (rhoWeight,rhoDB) = detachAndExtract(trace,scaffold.border[1],scaffold)
  @assert isa(rhoDB,DB)
  assertTorus(scaffold)

  xiWeights = (Float64)[]
  xiDBs = {}
  xiMixs = (Float64)[]
  

  for newValues = allSetsOfValues
    if (newValues == currentValues) continue end

    registerDeterministicLKernels(trace,scaffold,pnodes,newValues)
    push!(xiWeights,regenAndAttach(trace,scaffold.border[1],scaffold,false,DB()))
    push!(xiMixs,logDensityOfBlock(trace,scope,block))
    push!(xiDBs,detachAndExtract(trace,scaffold.border[1],scaffold)[2])
  end

  xiExpWeights = [exp(w) for w in xiWeights]
  rhoExpWeight = exp(rhoWeight)

  i = Distributions.rand(Distributions.Categorical(normalizeList(xiExpWeights)))
  (xiWeight,xiDB,xiMix) = (xiWeights[i],xiDBs[i],xiMixs[i])
  totalExpWeight = sum(xiExpWeights) + rhoExpWeight
  weightMinusRho = log(totalExpWeight - rhoExpWeight)
  weightMinusXi = log(totalExpWeight - xiExpWeights[i])

  if log(rand()) < (xiMix + weightMinusRho) - (rhoMix + weightMinusXi) # accept
    print(".")
    regenAndAttach(trace,scaffold.border[1],scaffold,true,xiDB)
  else # reject
    print("!")
    regenAndAttach(trace,scaffold.border[1],scaffold,true,rhoDB)
  end
  assertTrace(trace)
end

########## (3) PGibbs

# Construct ancestor path backwards
function constructAncestorPath(ancestorIndices,t::Int,p::Int)
  if (t == 1) return [] end
  path = [ancestorIndices[t,p]]

  for i in reverse(2:t-1)
    unshift!(path,ancestorIndices[i,path[1]])
  end

  @assert length(path) == t-1
  return path
end

# Restore the particle along the ancestor path
function restoreAncestorPath(trace::Trace,border,scaffold,omegaDBs,t,path::Array{Int})
  for i in 1:(t-1)
    selectedDB = omegaDBs[i,path[i]]
    regenAndAttach(trace,border[i],scaffold,true,selectedDB)
  end
end

# detach the rest of the particle
function detachRest(trace::Trace,border,scaffold,t::Int)
  for i = reverse(1:t-1)
    detachAndExtract(trace,border[i],scaffold)
  end
end

# P particles, not including RHO
# TODO for now, no resampling
# and then one final resampling step to select XI

function pGibbsInfer(trace::Trace,scope,arrayOfMutatingPNodes::Array{Set{Node}},P::Int)
  T = length(arrayOfMutatingPNodes)
  arrayOfPNodes = [copy(mutatingPNodes) for mutatingPNodes in arrayOfMutatingPNodes]
  assertTrace(trace)
  scaffold = constructScaffold(trace,arrayOfPNodes)

  rhoWeights = zeros(T)

  omegaDBs = cell(T,P+1)
  ancestorIndices = cell(T,P+1)

  # Compute all weights, DBs, and ESR_DBs for RHO
  for t = reverse(1:T)
    (rhoWeights[t],omegaDBs[t,P+1]) = detachAndExtract(trace,scaffold.border[t],scaffold)
    if t > 1
      ancestorIndices[t,P+1] = P+1
    end
  end

  assertTorus(scaffold)

  xiWeights = zeros(P)

  # Simulate and calculate initial xiWeights
  for p = 1:P
    regenAndAttach(trace,scaffold.border[1],scaffold,false,DB())
    (xiWeights[p],omegaDBs[1,p]) = detachAndExtract(trace,scaffold.border[1],scaffold)
  end

  # for every time step,
  for t = 2:T
    newXiWeights = zeros(P)
    # Sample new particle and propagate
    for p = 1:P
      extendedWeights = [xiWeights,rhoWeights[t-1]]
      # sample ancestor
      # might be nice to catch this as sample, and then construct path recursively from it.
      ancestorIndices[t,p] = Distributions.rand(Distributions.Categorical(normalizeList(map(exp,extendedWeights))))
      # restore ancestor
      path = constructAncestorPath(ancestorIndices,t,p)
      restoreAncestorPath(trace,scaffold.border,scaffold,omegaDBs,t,path)
      # propagate one time step
      regenAndAttach(trace,scaffold.border[t],scaffold,false,DB())
      # detach and extract the last sink
      (newXiWeights[p],omegaDBs[t,p]) = detachAndExtract(trace,scaffold.border[t],scaffold)

      # detach the rest of the sinks to yield the torus
      detachRest(trace,scaffold.border,scaffold,t)
    end
    xiWeights = newXiWeights
  end

  # Now sample a NEW particle in proportion to its weight
  xiExpWeights = [exp(w) for w in xiWeights]
  rhoExpWeight = exp(rhoWeights[T])

  i = Distributions.rand(Distributions.Categorical(normalizeList(xiExpWeights)))
  (xiWeight,xiDB) = (xiWeights[i],omegaDBs[i])
  totalExpWeight = sum(xiExpWeights) + rhoExpWeight
  weightMinusRho = log(totalExpWeight - rhoExpWeight)
  weightMinusXi = log(totalExpWeight - xiExpWeights[i])

  if log(rand()) < weightMinusRho - weightMinusXi # accept
    print(".")
    # TODO construct XI path
    path = [constructAncestorPath(ancestorIndices,T,i),i]
  else # reject
    print("!")
    # TODO construct RHO path
    path = [constructAncestorPath(ancestorIndices,T,P+1),P+1]
  end
  @assert length(path) == T
  restoreAncestorPath(trace,scaffold.border,scaffold,omegaDBs,T+1,path)
  assertTrace(trace)
end

