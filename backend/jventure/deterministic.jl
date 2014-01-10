regularOperators = [("Plus",+,"+"),
                    ("Minus",-,"-"),
                    ("Times",*,"*"),
                    ("Divides",/,"/"),
                    ("Pow",^,"pow"),
                    ("LessThan",<,"<"),
                    ("LessThanOrEqualTo",<=,"<="),
                    ("GreaterThan",>,">"),
                    ("GreaterThanOrEqual",>=,">="),
                    ("Not",!,"not"),
                    ("Equals",==,"=="),
                    ("NotEquals",!=,"!="),
                    ("Log",log,"log"),
                    ("Exp",exp,"exp"),
                    ("Min",min,"min"),
                    ("Max",max,"max"),
                    ("Abs",abs,"abs"),
]

## Add regular operators
for (prefix,op,sym) = regularOperators
  name = symbol(string(prefix,"OutputPSP"))
  @eval begin
    type $name <: OutputPSP end
    simulate(psp::$name,args::OutputArgs) = ($op)(args.operandValues...)
    builtInSPs[symbol($sym)] = SP(NullRequestPSP(),($name)(),($prefix))
  end
end
