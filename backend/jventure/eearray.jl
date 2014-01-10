import Base.length
import Base.delete!
import Base.push!

type EEArray{T}
  d::Dict{T,Int}
  v::Array{T}
end

function Base.push!(ee::EEArray,t)
  @assert !haskey(ee.d,t)
  ee.d[t] = length(ee.v) + 1
  push!(ee.v,t)
end

function Base.delete!(ee::EEArray,t)
  @assert haskey(ee.d,t)
  index = ee.d[t]
  lastIndex = length(ee.v)

  lastElem = ee.v[lastIndex]
  ee.d[lastElem] = index
  ee.v[index] = lastElem
  pop!(ee.v)
  delete!(ee.d,t)
  @assert length(ee.d) == length(ee.v)
end

sample(ee::EEArray) = ee.v[rand(1:length(ee))]
Base.length(ee::EEArray) = length(ee.v)
