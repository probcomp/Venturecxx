require("consistency.jl")
require("detach.jl")

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