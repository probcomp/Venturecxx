using PyCall
require("engine.jl")

function ConstructPyableEngine()
  engine = Engine()
  function myAssume(sym::String,exp_datum::String)
    assume(engine,sym,exp_datum)
  end
  function myPredict(exp_datum::String)
    predict(engine,exp_datum)
  end
  function myObserve(exp_datum::String,value) # TODO What's the type that Value needs to be?
    observe(engine,exp_datum,value)
  end
  function myReport(id::DirectiveID)
    report(engine,id)
  end
  function myInfer(N::Int64)
    infer(engine,N)
  end
  return [myAssume, myPredict, myObserve, myReport, myInfer]
end

@pyimport venture.cxx.wstests as wstests
function runWsTests(N)
  wstests.setUpJVentureBackend(ConstructPyableEngine)
  wstests.runTests(N)
end

runWsTests(ARGS[0])
