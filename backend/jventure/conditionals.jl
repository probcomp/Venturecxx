type BranchRequestPSP <: RequestPSP end
function simulate(psp::BranchRequestPSP,args::RequestArgs)
  expIndex = args.operandValues[1] ? 2 : 3
  exp = args.operandValues[expIndex]
  return Request((ESR)[ESR(args.node,exp,args.env)])
end

type BiplexOutputPSP <: OutputPSP end
function simulate(psp::BiplexOutputPSP,args::OutputArgs)
  return args.operandValues[args.operandValues[1] ? 2 : 3]
end

builtInSPs[symbol("branch")] = SP(BranchRequestPSP(),ESRRefOutputPSP(),"branch")
builtInSPs[symbol("biplex")] = SP(NullRequestPSP(),BiplexOutputPSP(),"biplex")