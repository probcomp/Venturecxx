regularOperators = [("Plus",+),
                    ("Minus",-),
                    ("Times",*),
                    ("Divides",/),
                    ("Pow",^),
                    ("LT",<),
                    ("LTE",<=),
                    ("GT",>),
                    ("GTE",>=),
                    ("Not",!),
                    ("EQ",==),
                    ("NotEQ",!=),
                    ("Log",log),
                    ("Exp",exp),
                    ("Min",min),
                    ("Max",max),
                    ("Abs",abs),

#                    ("Make_Map",Dict),
                    ("Map_Lookup",getindex),
                    ("Map_Contains",haskey),
                    ("Map_Size",length),

                    ("Make_Set",Set),
                    ("Set_Contains",(s,x)->in(x,s)),
                    ("Set_Size",length),

                    ("Vector_Lookup",getindex),
                    ("Vector_Length",length),


]

## Add regular operators
for (prefix,op) = regularOperators
  name = symbol(string(prefix,"OutputPSP"))
  @eval begin
    type $name <: OutputPSP end
    simulate(psp::$name,args::OutputArgs) = ($op)(args.operandValues...)
    builtInSPs[symbol(lowercase($prefix))] = SP(NullRequestPSP(),($name)(),(lowercase($prefix)))
  end
end


