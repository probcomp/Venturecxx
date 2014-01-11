type ApplyInScopeOutputPSP <: OutputPSP end

function simulate(psp::ApplyInScopeOutputPSP,args::OutputArgs)
  (scope::Any,block::Int,val::VentureValue) = args.operandValues
  return val
end

builtInSPs[symbol("apply_in_scope")] = SP(NullRequestPSP(),ApplyInScopeOutputPSP(),"apply_in_scope")

