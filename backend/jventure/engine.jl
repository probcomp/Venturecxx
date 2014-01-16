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
  logDensity = observe(engine.trace,baseAddr,sParse(value))
  if logDensity == -Inf
    error("Observe failed to constrain")
  end

  return baseAddr
end


function report_value(engine::Engine,id::DirectiveID)
  val = extractValue(engine.trace,id)
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
end

function infer(engine::Engine,params::Dict)
  if !haskey(params,"transitions") params["transitions"] = 1 end
  if params["kernel"] == "cycle"
    if !haskey(params,"subkernels") error("Cycle kernel must have things to cycle over ($params)") end
    for n = 1:params["transitions"]
      for k = params["subkernels"]
        infer(engine,k)
      end
    end
  else # A primitive infer expression
    set_default_params(params)
    infer(engine.trace,params)
  end
end

function reset(engine::Engine)
  engine.directiveCounter = 0
  engine.directives = (DirectiveID=>Any)[]
  engine.trace = Trace()
  return true
end

function set_default_params(params::Dict)
  if !haskey(params,"kernel") params["kernel"] = "mh" end
  if !haskey(params,"scope") params["scope"] = "default" end
  if !haskey(params,"block") params["block"] = "one" end
end
