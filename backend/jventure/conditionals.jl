type BranchRequestPSP <: RequestPSP end
function simulate(psp::BranchRequestPSP,args::RequestArgs)
  expIndex = args.operandValues[1] ? 2 : 3
  exp = args.operandValues[expIndex]
  return Request((ESR)[ESR(args.node,exp,args.env)])
end

builtInSPs[symbol("branch")] = SP(BranchRequestPSP(),ESRRefOutputPSP(),"branch")