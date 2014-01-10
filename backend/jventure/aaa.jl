### CollapsedMakeSymDirMult

type MakeSymDirMultOutputPSP <: OutputPSP end

simulate(psp::MakeSymDirMultOutputPSP,args::OutputArgs) = SP(NullRequestPSP(),SymDirMultOutputPSP(args.operandValues...),"make_sym_dir_mult")
childrenCanAAA(psp::MakeSymDirMultOutputPSP) = true

type SymDirMultOutputPSP <: RandomOutputPSP
  alpha::Float64
  K::Int64
end

constructSPAux(psp::SymDirMultOutputPSP) = (Float64)[0.0 for i in 1:psp.K]

function incorporate!(psp::SymDirMultOutputPSP,value::Int64,args::OutputArgs)
  @assert value > 0 && value <= length(args.spaux)
  args.spaux[value] += 1
end

unincorporate!(psp::SymDirMultOutputPSP,value::Int64,args::OutputArgs) = args.spaux[value] -= 1

function simulate(psp::SymDirMultOutputPSP,args::OutputArgs)
  counts = args.spaux + psp.alpha
  p = counts / sum(counts)
  return rand(Distributions.Categorical(p))
end

function logDensity(psp::SymDirMultOutputPSP,value::Int64,args::OutputArgs)
  counts = args.spaux + psp.alpha
  p = counts / sum(counts)
  return Distributions.logpdf(Distributions.Categorical(p),value)
end

function logDensityOfCounts(psp::SymDirMultOutputPSP,aux::Array{Float64})
  N = sum(aux)
  A = psp.alpha * psp.K
  x = lgamma(A) - lgamma(N+A)
  x += sum(lgamma(psp.alpha + aux)) - sum(lgamma(aux))
  return x
end
  

builtInSPs[symbol("make_sym_dir_mult")] = SP(NullRequestPSP(),MakeSymDirMultOutputPSP(),"make_sym_dir_mult")

############################## UncollapsedMakeSymDirMult

type MakeUSymDirMultOutputPSP <: OutputPSP end

function simulate(psp::MakeUSymDirMultOutputPSP,args::OutputArgs)
  (alpha,K) = args.operandValues
  theta = Distributions.rand(Distributions.Dirichlet(K,alpha))
  return SP(NullRequestPSP(),USymDirMultOutputPSP(theta),"make_usym_dir_mult")
end

function logDensity(psp::MakeUSymDirMultOutputPSP,value::SP,args::OutputArgs)
  (alpha,K) = args.operandValues
  d = Distributions.Dirichlet(K,alpha)
  theta = value.outputPSP.theta
  ld = Distributions.logpdf(d,theta)
  return ld
end

type USymDirMultOutputPSP <: RandomOutputPSP
  theta::Array{Float64}
end

constructSPAux(psp::USymDirMultOutputPSP) = (Float64)[0.0 for i in 1:length(psp.theta)]

incorporate!(psp::USymDirMultOutputPSP,value::Int64,args::OutputArgs) = args.spaux[value] += 1
unincorporate!(psp::USymDirMultOutputPSP,value::Int64,args::OutputArgs) = args.spaux[value] -= 1

simulate(psp::USymDirMultOutputPSP,args::OutputArgs) = Distributions.rand(Distributions.Categorical(psp.theta))
logDensity(psp::USymDirMultOutputPSP,value::Int64,args::OutputArgs) = Distributions.logpdf(Distributions.Categorical(psp.theta),value)

hasAEKernel(psp::USymDirMultOutputPSP) = true
function AEInfer(psp::USymDirMultOutputPSP,args::OutputArgs)
  counts = args.madeSPAux + args.operandValues[1]
  p = counts / sum(counts)
  psp.theta = Distributions.rand(Distributions.Dirichlet(p))
end

builtInSPs[symbol("make_usym_dir_mult")] = SP(NullRequestPSP(),MakeUSymDirMultOutputPSP(),"make_usym_dir_mult")



