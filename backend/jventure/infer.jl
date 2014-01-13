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


function enumerativeGibbsInfer(trace::Trace,scope,block,mutating_pnodes::Set{Node})
  pnodes = copy(mutating_pnodes)
  assertTrace(trace)
  rhoMix = logDensityOfBlock(trace,scope,block)
  scaffold = constructScaffold(trace,pnodes)

  currentValues = getCurrentValues(trace,pnodes)
  allSetsOfValues = getCartesianProductOfEnumeratedValues(trace,pnodes)

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

########## (3) PGibbs

# # TODO CURRENT SPOT

# # Construct ancestor path backwards
# def constructAncestorPath(ancestorIndices,t,n):
#   if t > 0: path = [ancestorIndices[t][n]]
#   else: path = []

#   for i in reversed(range(1,t)): path.insert(0, ancestorIndices[i][path[0]])
#   assert len(path) == t
#   return path

# # Restore the particle along the ancestor path
# def restoreAncestorPath(trace,sinks,drg,omegaDBs,omegaESR_DBs,t,path):
#   for i in range(t):
#     selectedDB = omegaDBs[i][path[i]]
#     selectedESR_DB = omegaESR_DBs[i][path[i]]
        
#     regen(trace,sinks[i],drg,True,selectedDB,selectedESR_DB)

# # detach the rest of the particle
# def detachRest(trace,sinks,drg,t):
#   for i in reversed(range(t)): 
#     detach(trace,sinks[i],drg)

# # split the sinks into groups, and return the number of 
# # time steps settled on.
# def splitSinks(drg,T):
#   allSinks = drg.sinks()
#   sinks = utilities.splitListIntoGroups(allSinks,T)
#   T = len(sinks)
#   return sinks, T

# # P particles, not including RHO
# # T groups of sinks, with T-1 resampling steps
# # and then one final resampling step to select XI
# def pGibbsInfer(trace,P,T,depth):
#   (principalNode,ldRho) = trace.samplePrincipalNode()
#   drg = constructDRG(trace,[principalNode],depth)
#   sinks,T = splitSinks(drg,T)

#   rhoDBs = [None for t in range(T)]
#   rhoESR_DBs = [None for t in range(T)]
#   weightsRho = [None for t in range(T)]

#   # Compute all weights, DBs, and ESR_DBs for RHO
#   for t in reversed(range(T)):
#     (rhoDBs[t],rhoESR_DBs[t],weightsRho[t]) = detach(trace,sinks[t],drg)

#   assertRegenCountsZero(trace,drg)

#   omegaDBs = [[None for n in range(P)] + [rhoDBs[t]] for t in range(T)] 
#   omegaESR_DBs = [[None for n in range(P)] + [rhoESR_DBs[t]]for t in range(T)]
#   ancestorIndices = [[None for n in range(P)] + [P] for t in range(T)]
#   weights = [0 for n in range(P)]

#   ldOmegas = [0 for n in range(P)]

#   # Simulate and calculate initial weights
#   for n in range(P):
#     weightRegen = regen(trace,sinks[0],drg,False)
#     ldOmegas[n] = trace.logDensityOfPrincipalNode(principalNode)
#     (omegaDBs[0][n],omegaESR_DBs[0][n],weights[n]) = detach(trace,sinks[0],drg)
#     assert abs(weightRegen - weights[n]) < .00001
    

#   # for every time step,
#   for t in range(1,T):
#     newWeights = [0 for n in range(P)]
#     # Sample new particle and propagate
#     for n in range(P):
#       extendedWeights = weights + [weightsRho[t-1]]
#       # sample ancestor
#       # might be nice to catch this as sample, and then construct path recursively from it.
#       ancestorIndices[t][n] = Categorical(utilities.mapExp(extendedWeights),range(P+1))
#       # restore ancestor
#       path = constructAncestorPath(ancestorIndices,t,n)
#       restoreAncestorPath(trace,sinks,drg,omegaDBs,omegaESR_DBs,t,path)
#       # propagate one time step
#       weightRegen = regen(trace,sinks[t],drg,False)
#       # only needed the last time
#       ldOmegas[n] = trace.logDensityOfPrincipalNode(principalNode)
#       # detach and extract the last sink
#       (omegaDBs[t][n],omegaESR_DBs[t][n],newWeights[n]) = detach(trace,sinks[t],drg)
      
#       assert abs(weightRegen - newWeights[n]) < .00001

#       # detach the rest of the sinks to yield the torus
#       detachRest(trace,sinks,drg,t)

#     weights = newWeights

#   # Now sample a NEW particle in proportion to its weight
#   finalIndex = Categorical(utilities.mapExp(weights),range(P))
#   weightRho = weightsRho[T-1]
#   weightXi = weights[finalIndex]

#   ldXi = ldOmegas[finalIndex]
  
#   weightMinusXi = math.log(sum(utilities.mapExp(weights)) + math.exp(weightRho) - math.exp(weightXi))
#   weightMinusRho = math.log(sum(utilities.mapExp(weights)))

#   alpha = (ldXi + weightMinusRho) - (ldRho + weightMinusXi)

#   print "alpha: " + str(alpha)

#   # TODO URGENT need to do much more thorough flushing!
#   # Everytime a DB is abandoned we need to flush.
#   if math.log(random.random()) < alpha: # accept
#     path = constructAncestorPath(ancestorIndices,T-1,finalIndex) + [finalIndex]
# #    print "(path,T): " + str(path)
#   else: # reject
#     path = constructAncestorPath(ancestorIndices,T-1,P) + [P]
# #    print "should be all P: " + str(path)
    
#   assert len(path) == T
#   restoreAncestorPath(trace,sinks,drg,omegaDBs,omegaESR_DBs,T,path)
#   assertNoUndefineds(trace,drg)




