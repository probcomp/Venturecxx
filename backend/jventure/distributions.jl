import Distributions

regularDistributions = [("Normal",Distributions.Normal),
                 ("Beta",Distributions.Beta),
                 ("Laplace",Distributions.Laplace),
                 ("Uniform",Distributions.Uniform),
                 ("Gamma",Distributions.Gamma),
#                 ("Bernoulli",Distributions.Bernoulli),
                 ("Categorical",Distributions.Categorical),
                 ("Uniform_Discrete",Distributions.DiscreteUniform),
                 ("Geometric",Distributions.Geometric),
                 ("Dirichlet",Distributions.Dirichlet),
                        ]

## Add binary-absorbing
for (prefix,d) = regularDistributions
  name = symbol(string(prefix,"OutputPSP"))
  @eval begin
    type $name <: RandomOutputPSP end
    simulate(psp::$name,args::OutputArgs) = Distributions.rand(($d)(args.operandValues...))
    logDensity(psp::$name,value::Any,args::OutputArgs) = Distributions.logpdf(($d)(args.operandValues...),value)
    builtInSPs[symbol(lowercase($prefix))] = SP(NullRequestPSP(),($name)(),(lowercase($prefix)))
  end
end

## Flip
## TODO allow an injective function on top of a Distribution in a canonical way
type FlipOutputPSP <: RandomOutputPSP end
simulate(psp::FlipOutputPSP,args::OutputArgs) = Distributions.rand(Distributions.Bernoulli(args.operandValues...)) == 1
logDensity(psp::FlipOutputPSP,value::Any,args::OutputArgs) = Distributions.logpdf(Distributions.Bernoulli(args.operandValues...),value ? 1 : 0)
builtInSPs[:bernoulli] = SP(NullRequestPSP(),FlipOutputPSP(),"flip")


## Enumeration
enumerateValues(psp::CategoricalOutputPSP,args::OutputArgs) = [i for i in 1:length(args.operandValues)]

# function enumerateValues(psp::BernoulliOutputPSP,args::OutputArgs)
#   if isempty(args.operandValues)
#     return [1,0]
#   elseif args.operandValues[1] == 0
#     return [0]
#   elseif args.operandValues[1] == 1
#     return [0]
#   else
#     return [1,0]
#   end
# end
