require("engine.jl")
using Debug

# sivm = Engine()
# (id,value) = predict(sivm,"(+ 11 22)")
# println(string("should be 33: ",value))
# @assert report(sivm,id) == 33

# sivm = Engine()
# (id,value) = predict(sivm,"(* 11 4)")
# println(string("should be 44: ",value))
# @assert report(sivm,id) == 44

# sivm = Engine()
# (id,value) = predict(sivm,"(< 11 (+ 4 6))")
# println(string("should be false: ",value))
# @assert !report(sivm,id)

# sivm = Engine()
# (id,value) = predict(sivm,"(== 11 (+ 4 7))")
# println(string("should be true: ",value))
# @assert report(sivm,id)

function normalizeList(seq)
  denom = sum(seq)
  if denom > 0
    return [x/denom for x in seq]
  else
    return [0 for x in seq]
  end
end


sivm = Engine()
(id,value) = predict(sivm,"((if (== (bernoulli 0.5) 1) (lambda (x y) (normal x y)) normal) 0 1)")
ps = loggingInfer(sivm.trace,id,1000)
#println(ps)
println(string(mean(ps),"  ||  ",var(ps)))

# sivm = Engine()
# (id,value) = predict(sivm,"(normal (normal (normal 0 1) (gamma 1 1)) (gamma 1 1))")
# ps = loggingInfer(sivm.trace,id,5000)
# #println(ps)
# println(string(mean(ps),"  ||  ",var(ps)))




# sivm = Engine()
# (id,value) = predict(sivm,"(laplace 1 1)")
# println(string("should be |x|<100: ",value))
# @assert abs(report(sivm,id)) < 100

# sivm = Engine()
# (id,value) = predict(sivm,"(* (beta 1 1) (beta 5 5))")
# println(string("should be |x|<1: ",value))
# @assert abs(report(sivm,id)) < 1
 