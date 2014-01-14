require("trace.jl")
require("parse.jl")
require("sparse.jl")


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

function assume(engine::Engine,sym::String,exp_datum)
  baseAddr = nextBaseAddr(engine)
  engine.directives[baseAddr] = {"assume",sym,exp_datum}

  exp = sParse(exp_datum)

  evalExpression(engine.trace,baseAddr,exp)
  bindInGlobalEnv(engine.trace,symbol(sym),baseAddr)

  return (engine.directiveCounter,report_value(engine,baseAddr))
end

function predict(engine::Engine,exp_datum)
  baseAddr = nextBaseAddr(engine)
  engine.directives[baseAddr] = {"predict",exp_datum}

  exp = sParse(exp_datum)

  evalExpression(engine.trace,baseAddr,exp)
  println("evaluated")
  return (engine.directiveCounter,report_value(engine,baseAddr))
end

function observe(engine::Engine,exp_datum,value::VentureValue)
  baseAddr = nextBaseAddr(engine)
  engine.directives[baseAddr] = {"observe",exp_datum,value}

  exp = sParse(exp_datum)

  evalExpression(engine.trace,baseAddr,exp)
  logDensity = observe(engine.trace,baseAddr,value)
  if logDensity == -Inf
    error("Observe failed to constrain")
  end

  return baseAddr
end


function report_value(engine::Engine,id::DirectiveID)
  val = extractValue(engine.trace,id)
  println("[JL-START]")
  println(string("report_value: ",val,typeof(val)))
  if isa(val,Bool)
    return { "type"=>"boolean", "value" => val }
  elseif isa(val,Number)
    return { "type"=>"number", "value" => val }
  elseif isa(val,Union(String,Symbol))
    return { "type"=>"symbol", "value" => val }
  elseif isa(val,SPRef)
    return { "type"=>"sp", "value"=>"<sp>" }
  else
    return { "type"=>"unknown", "value"=>"<unknown>" }
  end
  println("[JL-END]")
end

infer(engine::Engine,N::Int64) = infer(engine.trace,N::Int64)
