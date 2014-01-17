### CollapsedMakeSymDirMult

abstract DirMultOutputPSP <: RandomOutputPSP
constructSPAux(psp::DirMultOutputPSP) = (Float64)[0.0 for i in 1:getK(psp)]
incorporate!(psp::DirMultOutputPSP,value::Int64,args::OutputArgs) = args.spaux[value] += 1
unincorporate!(psp::DirMultOutputPSP,value::Int64,args::OutputArgs) = args.spaux[value] -= 1

type MakeSymDirMultOutputPSP <: OutputPSP end

simulate(psp::MakeSymDirMultOutputPSP,args::OutputArgs) = SP(NullRequestPSP(),SymDirMultOutputPSP(args.operandValues...),"make_sym_dir_mult")
childrenCanAAA(psp::MakeSymDirMultOutputPSP) = true

type SymDirMultOutputPSP <: DirMultOutputPSP
  alpha::Float64
  K::Int64
end

getK(psp::SymDirMultOutputPSP) = psp.K

function simulate(psp::SymDirMultOutputPSP,args::OutputArgs)
  counts = args.spaux + psp.alpha
  p = counts / sum(counts)
  retval = Distributions.rand(Distributions.Categorical(p))
  @assert retval <= psp.K
  return retval
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
require("lkernel.jl")

type MakeUSymDirMultOutputPSP <: RandomOutputPSP end

childrenCanAAA(psp::MakeUSymDirMultOutputPSP) = true
getAAALKernel(psp::MakeUSymDirMultOutputPSP) = MakeUSymDirMultAAALKernel()

function simulate(psp::MakeUSymDirMultOutputPSP,args::OutputArgs)
  (alpha,K) = args.operandValues
  theta = Distributions.rand(Distributions.Dirichlet(int(K),alpha))
  @assert length(theta) == K
  return SP(NullRequestPSP(),USymDirMultOutputPSP(theta),"make_uc_sym_dir_mult")
end

function logDensity(psp::MakeUSymDirMultOutputPSP,value::SP,args::OutputArgs)
  (alpha,K) = args.operandValues
  d = Distributions.Dirichlet(int(K),alpha)
  theta = value.outputPSP.theta
  ld = Distributions.logpdf(d,theta)
  return ld
end

type MakeUSymDirMultAAALKernel <: LKernel end
function ksimulate(k::MakeUSymDirMultAAALKernel,trace::Trace,oldValue::SP,args::Args)
  (alpha,K) = args.operandValues
  counts = args.madeSPAux + alpha
  theta = rand(Distributions.Dirichlet(counts))
  return SP(NullRequestPSP(),USymDirMultOutputPSP(theta),"make_uc_sym_dir_mult")
end

type USymDirMultOutputPSP <: DirMultOutputPSP
  theta::Array{Float64}
end

getK(psp::USymDirMultOutputPSP) = length(psp.theta)

simulate(psp::USymDirMultOutputPSP,args::OutputArgs) = Distributions.rand(Distributions.Categorical(psp.theta))
logDensity(psp::USymDirMultOutputPSP,value::Int64,args::OutputArgs) = Distributions.logpdf(Distributions.Categorical(psp.theta),value)

builtInSPs[symbol("make_uc_sym_dir_mult")] = SP(NullRequestPSP(),MakeUSymDirMultOutputPSP(),"make_uc_sym_dir_mult")



