# isVariable must precede isSelfEvaluating

isVariable(sym::Symbol) = true
isVariable(x::VentureValue) = false

isSelfEvaluating(xs::Array{VentureValue}) = false
isSelfEvaluating(x::VentureValue) = true

isQuotation(xs::Array{VentureValue}) = (xs[1] == :quote)
textOfQuotation(xs::Array{VentureValue}) = xs[2]

getOperator(xs::Array{VentureValue}) = xs[1]
getOperands(xs::Array{VentureValue}) = xs[2:]