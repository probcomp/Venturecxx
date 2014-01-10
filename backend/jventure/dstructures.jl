## vector of floats
type MakeFloatArrayOutputPSP <: OutputPSP end
simulate(psp::MakeFloatArrayOutputPSP,args::OutputArgs) = convert(Array{Float64},args.operandValues)
builtInSPs[symbol("float_array")] = SP(NullRequestPSP(),MakeFloatArrayOutputPSP(),"float_array")

