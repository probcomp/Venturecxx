abstract Args

type RequestArgs <: Args
  node::Node
  operandValues::Array{VentureValue}
  operandNodes::Array{Node}
  spaux::Any
  env::ExtendedEnvironment
end

type OutputArgs <: Args
  node::Node
  operandValues::Array{VentureValue}
  operandNodes::Array{Node}

  requestValue::Request
  esrParentValues::Array{VentureValue}
  esrParentNodes::Array{Node}

  madeSPAux::Any
  spaux::Any
  env::ExtendedEnvironment
end

