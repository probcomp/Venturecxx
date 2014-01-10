type MakeMSPOutputPSP <: OutputPSP end

simulate(psp::MakeMSPOutputPSP,args::OutputArgs) = SP(MSPRequestPSP(args.operandNodes[1]),ESRRefOutputPSP(),"msp")

type MSPRequestPSP <: RequestPSP
  sharedOperatorNode::Node
end

function simulate(psp::MSPRequestPSP,args::RequestArgs)
  id = args.operandValues
  exp = vcat([:memoizedSP],args.operandValues)
  env = ExtendedEnvironment((Symbol=>Node)[:memoizedSP=>psp.sharedOperatorNode],EmptyEnvironment())
  return Request([ESR(id,exp,env)])
end

builtInSPs[symbol("mem")] = SP(NullRequestPSP(),MakeMSPOutputPSP(),"mem")