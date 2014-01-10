require("consistency.jl")
require("detach.jl")

function mhInfer(trace::Trace,pnode::ApplicationNode)
  assertTrace(trace)
  rhoMix = logDensityOfPrincipalNode(trace,pnode)
  scaffold = constructScaffold(trace,Set{Node}(pnode))
  (rhoWeight,rhoDB) = detachAndExtract(trace,scaffold.border,scaffold)
  assertTorus(scaffold)
  xiWeight = regenAndAttach(trace,scaffold.border,scaffold,false,rhoDB)
  assertTrace(trace)
  xiMix = logDensityOfPrincipalNode(trace,pnode)
  if log(rand()) > (xiMix + xiWeight) - (rhoMix + rhoWeight) # reject
    detachAndExtract(trace,scaffold.border,scaffold)
    assertTorus(scaffold)
    regenAndAttach(trace,scaffold.border,scaffold,true,rhoDB)
    assertTrace(trace)
  end
end