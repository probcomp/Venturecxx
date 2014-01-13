require("args.jl")

abstract PSP
abstract RequestPSP <: PSP
abstract OutputPSP <: PSP
abstract RandomOutputPSP <: OutputPSP

typealias SPFamilyID Any

simulate(psp::PSP,args::Args) = error("A psp must override simulate")
logDensity(psp::PSP,value::VentureValue,args::Args) = 0.0

incorporate!(psp::PSP,value::VentureValue,args::Args) = nothing
unincorporate!(psp::PSP,value::VentureValue,args::Args) = nothing

isRandom(psp::PSP) = false
canAbsorb(psp::PSP) = false
isRandom(psp::RandomOutputPSP) = true
canAbsorb(psp::RandomOutputPSP) = true

type NullRequestPSP <: RequestPSP end
simulate(psp::NullRequestPSP,args::Args) = Request((ESR)[])
canAbsorb(psp::NullRequestPSP) = true

type ESRRefOutputPSP <: OutputPSP end
function simulate(psp::ESRRefOutputPSP,args::Args) 
  @assert length(args.esrParentValues) == 1
  args.esrParentValues[1]
end

childrenCanAAA(psp::PSP) = false

constructSPAux(psp::OutputPSP) = nothing # just so that SPs don't need to be abstract

hasAEKernel(psp::OutputPSP) = false

enumerateValues(psp::PSP,args::Args) = error("PSP cannot enumerate values.")
