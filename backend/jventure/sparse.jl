# "Stack" Parse
# (undo the damage that the stack did)
require("parse.jl")

function sParse(x)
  result =  sParseHelper(x)
  dresult = desugar(result)

  println("[JL-START]")
  print("before: ") ; show(x) ; println(string(",  ",typeof(x)))
  print("mid: ") ; show(result) ; println(string(",  ",typeof(result)))
  print("after: ") ; show(dresult) ; println(string(",  ",typeof(dresult)))
  print("[JL-END]")

  return dresult
end

function nest(a::Array)
  if ndims(a) > 1
    @assert ndims(a) == 1
    b = Array(Any,1)
    for i = 1:size(a)[1]
      c = a[i:]
      for j = 1:size(a)[2]
        push!(c,a[i,j])
        
  end


end

sParseHelper(a::Array) = [sParseHelper(x) for x in a]
sParseHelper(d::Dict) = isa(d["value"],String) ? symbol(d["value"]) : d["value"]
