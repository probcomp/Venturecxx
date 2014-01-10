import Distributions

regularDistributions = [("normal",Distributions.Normal),
                 ("beta",Distributions.Beta),
                 ("laplace",Distributions.Laplace),
                 ("uniform",Distributions.Uniform),
                 ("gamma",Distributions.Gamma),
                 ("bernoulli",Distributions.Bernoulli),
                 ("categorical",Distributions.Categorical),
                 ("uniform_discrete",Distributions.DiscreteUniform),
                 ("geometric",Distributions.Geometric),
                 ("dirichlet",Distributions.Dirichlet),
                        ]

## Add binary-absorbing
for (prefix,d) = regularDistributions
  name = symbol(string(prefix,"OutputPSP"))
  @eval begin
    type $name <: RandomOutputPSP end
    simulate(psp::$name,args::OutputArgs) = Distributions.rand(($d)(args.operandValues...))
    logDensity(psp::$name,value::Any,args::OutputArgs) = Distributions.logpdf(($d)(args.operandValues...),value)
    builtInSPs[symbol($prefix)] = SP(NullRequestPSP(),($name)(),($prefix))
  end
end

## Flip
type FlipOutputPSP <: RandomOutputPSP end
simulate(psp::FlipOutputPSP,args::OutputArgs) = Distributions.rand(Distributions.Bernoulli(args.operandValues...)) == 1
logDensity(psp::FlipOutputPSP,value::Any,args::OutputArgs) = Distributions.logpdf(Distributions.Bernoulli(args.operandValues...),value ? 1 : 0)
builtInSPs[:flip] = SP(NullRequestPSP(),FlipOutputPSP(),"flip")

