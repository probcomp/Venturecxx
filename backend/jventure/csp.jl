type CSPRequestPSP <: RequestPSP
  ids::Array{VentureValue}
  exp::VentureValue
  env::ExtendedEnvironment
end

function simulate(psp::CSPRequestPSP,args::RequestArgs)
  extendedEnv = ExtendedEnvironment(psp.env,psp.ids,args.operandNodes)
  return Request((ESR)[ESR(args.node,psp.exp,extendedEnv)])
end

type MakeCSPOutputPSP <: OutputPSP end
function simulate(psp::MakeCSPOutputPSP,args::OutputArgs)
  (ids,exp) = args.operandValues[1:2]
  return SP(CSPRequestPSP(ids,exp,args.env),ESRRefOutputPSP(),"csp")
end

builtInSPs[symbol("make_csp")] = SP(NullRequestPSP(),MakeCSPOutputPSP(),"make_csp")
