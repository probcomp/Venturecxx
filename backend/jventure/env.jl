abstract Environment
require("value.jl")

type EmptyEnvironment <: Environment
end

type ExtendedEnvironment <: Environment
  frame::Dict{Symbol,Node}
  outerEnv::Environment
end

function ExtendedEnvironment(env::ExtendedEnvironment,syms::Array{VentureValue},nodes::Array{Node})
  return ExtendedEnvironment((Symbol=>Node)[sym => node for (sym,node) in zip(syms,nodes)],env)
end

findSymbol(env::ExtendedEnvironment,sym::Symbol) = haskey(env.frame,sym) ? env.frame[sym] : findSymbol(env.outerEnv,sym)
findSymbol(env::EmptyEnvironment,sym::Symbol) = error("Cannot find: " * string(sym))

function addBinding!(env::ExtendedEnvironment,sym::Symbol,node::Node)
  env.frame[sym] = node
end
