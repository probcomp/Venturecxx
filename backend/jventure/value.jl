# No latents yet

typealias VentureValue Any

type ESR
  id::VentureValue
  exp::VentureValue
  env::Environment
  scope::VentureValue
  block::VentureValue
end

ESR(id::VentureValue,exp::VentureValue,env::Environment) = ESR(id,exp,env,nothing,nothing)

type Request
  esrs::Array{ESR}
end

