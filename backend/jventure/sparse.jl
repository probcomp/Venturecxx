# "Stack" Parse
# (undo the damage that the stack did)
sParse(a::Array) = [sParse(x) for x in a]
sParse(d::Dict) = isa(d["value"],String) ? symbol(d["value"]) : d["value"]
