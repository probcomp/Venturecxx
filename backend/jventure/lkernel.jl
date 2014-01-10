abstract LKernel
ksimulate(k::LKernel,trace::Trace,oldValue::VentureValue,args::Args) = error("abstract method")
kweight(k::LKernel,trace::Trace,newValue::VentureValue,oldValue::VentureValue,args::Args) = 0.0
kreverseWeight(k::LKernel,trace::Trace,oldValue::VentureValue,args::Args) = kweight(k,trace,oldValue,nothing,args)

type DefaultAAALKernel <: LKernel
  makerPSP::OutputPSP
end

ksimulate(k::DefaultAAALKernel,trace::Trace,oldValue::Union(SP,Nothing),args::OutputArgs) = simulate(k.makerPSP,args)
function kweight(k::DefaultAAALKernel,trace::Trace,newValue::SP,oldValue::Union(SP,Nothing),args::OutputArgs)
  return logDensityOfCounts(newValue.outputPSP,args.madeSPAux)
end

getAAALKernel(psp::OutputPSP) = DefaultAAALKernel(psp)