vparse(s::String) = read_from(tokenize(s))

tokenize(s::String) = convert(Array{Any},split(replace(replace(s,"("," ( "),")"," ) ")))

function read_from(tokens::Array{Any})
  if isempty(tokens)
    error("unexpeted EOF while reading")
  else
    token = shift!(tokens)
    if token == "("
      L = Array(Any,0)
      while tokens[1] != ")"
        push!(L,read_from(tokens))
      end
      shift!(tokens) # pop ")"
      return L # returns an Array{Any}
    elseif token == ")"
      error("unexpeted )")
    else
      return atom(token)
    end
  end
end

function atom(token::String)
  if token == "if"
    return symbol("if")
  elseif token == "quote"
    return symbol("quote")
  else 
    return parse(token)
  end
end

# Need to overwrite parse to handle some weird cases
# if,quote

function desugar(exp::Array{Any})
  if isempty(exp)
    return exp
  elseif exp[1] == :lambda
    ids = (Any)[:quote,exp[2]]
    body = (Any)[:quote,desugar(exp[3])]
    return (Any)[:make_csp,ids,body]
  elseif exp[1] == :if
    cond = (Any)[:quote,desugar(exp[3])]
    alt = (Any)[:quote,desugar(exp[4])]
    return (Any)[:branch,desugar(exp[2]),cond,alt]
  else
    return [desugar(subexp) for subexp = exp]
  end
end
desugar(exp::Any) = exp


vunparse(exp::Array{Any}) = "(" * join([vunparse(subexp) for subexp = exp]," ") * ")"
vunparse(exp::Any) = string(x)

#println(vparse("10"))
#println(vparse("(+ 5 5)"))
#println(vparse("(* 2 5)"))
#println(vparse("((lambda (x) x) 10)"))
#println(vparse("(+ ((lambda (x y) (* x y)) 3 2) 3 1)"))

#println(desugar(vparse("10")))
#println(desugar(vparse("(lambda (x) x)")))
#println(desugar(vparse("(vif x 1 2)")))
#println(desugar(vparse("((lambda (x) x) 10)")))
#println(desugar(vparse("(+ ((lambda (x y) (* x y)) 3 2) 3 1)")))
#println(desugar(vparse("((lambda (x) (if (< x 10) 1 2)) 10)")))


