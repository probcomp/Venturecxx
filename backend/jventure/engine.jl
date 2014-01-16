require("trace.jl")
require("parse.jl")

type Engine
  directiveCounter::DirectiveID
  directives::Dict{DirectiveID,Any}
  trace::Trace
end


function Engine()
  sivm = Engine(0,(DirectiveID=>Any)[],Trace())
#  assume(sivm,"noisy_true","(lambda (pred noise) (flip (if pred 1.0 noise)))")
  return sivm
end

function nextBaseAddr(engine::Engine)
  engine.directiveCounter += 1
  return engine.directiveCounter
end

function assume(engine::Engine,sym::String,exp_datum::String)
  baseAddr = nextBaseAddr(engine)
  engine.directives[baseAddr] = ["assume",sym,exp_datum]

  exp = desugar(vparse(exp_datum))

  evalExpression(engine.trace,baseAddr,exp)
  bindInGlobalEnv(engine.trace,symbol(sym),baseAddr)

  return (engine.directiveCounter,extractValue(engine.trace,baseAddr))
end

function predict(engine::Engine,exp_datum::String)
  baseAddr = nextBaseAddr(engine)
  engine.directives[baseAddr] = ["predict",exp_datum]

  exp = desugar(vparse(exp_datum))

  evalExpression(engine.trace,baseAddr,exp)
  return (engine.directiveCounter,extractValue(engine.trace,baseAddr))
end

function observe(engine::Engine,exp_datum::String,value::VentureValue)
  baseAddr = nextBaseAddr(engine)
  engine.directives[baseAddr] = ["observe",exp_datum,value]

  exp = desugar(vparse(exp_datum))

  evalExpression(engine.trace,baseAddr,exp)
  logDensity = observe(engine.trace,baseAddr,value)
  if logDensity == -Inf
    error("Observe failed to constrain")
  end

  return baseAddr
end

report(engine::Engine,id::DirectiveID) = extractValue(engine.trace,id)
infer(engine::Engine,N::Int64) = infer(engine.trace,N::Int64)
