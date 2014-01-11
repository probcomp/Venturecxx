import Base.length
import Base.delete!
import Base.haskey
import Base.setindex!
import Base.isempty
import Base.getindex

type SMap{K,T}
  d::Dict{K,Int}
  v::Array{(K,T)}
end

constructSMap(K,T) = SMap{K,T}(Dict{K,Int}(),Array((K,T),0))

function Base.setindex!{K,T}(sm::SMap{K,T},t::T,k)
  @assert !haskey(sm.d,k)
  sm.d[k] = length(sm.v) + 1
  push!(sm.v,(k,t))
end

function Base.delete!{K,T}(sm::SMap{K,T},k)
  @assert haskey(sm.d,k)
  index = sm.d[k]
  lastIndex = length(sm.v)

  lastPair = sm.v[lastIndex]
  sm.d[lastPair[1]] = index
  sm.v[index] = lastPair
  pop!(sm.v)
  delete!(sm.d,k)
  @assert length(sm.d) == length(sm.v)
end


## TODO not sure why this did not work with k::K
Base.haskey{K,T}(sm::SMap{K,T},k) = haskey(sm.d,k)
Base.isempty{K,T}(sm::SMap{K,T}) = isempty(sm.v)

Base.getindex{K,T}(sm::SMap{K,T},k) = sm.v[sm.d[k]][2]

sample{K,T}(sm::SMap{K,T}) = sm.v[rand(1:length(sm))]
Base.length{K,T}(sm::SMap{K,T}) = length(sm.v)
