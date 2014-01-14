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
                    ("Equals",==),
                    ("NotEquals",!=),
                    ("Log",log),
                    ("Exp",exp),
                    ("Min",min),
                    ("Max",max),
                    ("Abs",abs),
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
