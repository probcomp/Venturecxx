# No latents yet

typealias VentureValue Any

type ESR
  id::VentureValue
  exp::VentureValue
  env::Environment
end

type Request
  esrs::Array{ESR}
end

