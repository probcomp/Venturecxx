import Base.length
import Base.isempty
import Base.getindex
import Base.start
import Base.next
import Base.done

############################### simplex point
type SimplexOutputPSP <: OutputPSP end
simulate(psp::SimplexOutputPSP,args::OutputArgs) = convert(Array{Float64},args.operandValues)
builtInSPs[symbol("simplex")] = SP(NullRequestPSP(),SimplexOutputPSP(),"simplex")



############################### list


abstract VentureList
type VentureNil <: VentureList end
type VenturePair <: VentureList
  car::Any
  cdr::VentureList
end

Base.start(vs::VentureList) = vs
Base.next(iter::VentureList,state::VentureList) = (state.car,state.cdr)
Base.done(iter::VentureList,state::VentureNil) = true
Base.done(iter::VentureList,state::VenturePair) = false


function makeVentureList(xs::Array)
  if isempty(xs)
    return VentureNil()
  else 
    return VenturePair(xs[1],makeVentureList(xs[2:end]))
  end
end

function Base.length(vs::VentureList)
  if isa(vs,VentureNil) return 0 end
  return 1 + length(vs.cdr)
end

function Base.getindex(vs::VentureList,i::Int)
  if i == 1
    return vs.car
  else
    return vs.cdr[i-1]
  end
end

function ventureListToArray(vs::VentureList)
  xs = {}
  while isa(vs,VenturePair)
    push!(xs,vs.car)
    vs = vs.cdr
  end
  @assert isa(vs,VentureNil)
  return xs
end
  
type ListOutputPSP <: OutputPSP end
simulate(psp::ListOutputPSP,args::OutputArgs) = makeVentureList(args.operandValues)
builtInSPs[symbol("list")] = SP(NullRequestPSP(),ListOutputPSP(),"list")

type PairOutputPSP <: OutputPSP end
simulate(psp::PairOutputPSP,args::OutputArgs) = VenturePair(args.operandValues[1],args.operandValues[2])
builtInSPs[symbol("pair")] = SP(NullRequestPSP(),PairOutputPSP(),"pair")

type FirstOutputPSP <: OutputPSP end
simulate(psp::FirstOutputPSP,args::OutputArgs) = args.operandValues[1].car
builtInSPs[symbol("first")] = SP(NullRequestPSP(),FirstOutputPSP(),"first")

type RestOutputPSP <: OutputPSP end
simulate(psp::RestOutputPSP,args::OutputArgs) = args.operandValues[1].cdr
builtInSPs[symbol("rest")] = SP(NullRequestPSP(),RestOutputPSP(),"rest")

type IsPairOutputPSP <: OutputPSP end
simulate(psp::IsPairOutputPSP,args::OutputArgs) = isa(args.operandValues[1],VenturePair)
builtInSPs[symbol("is_pair")] = SP(NullRequestPSP(),IsPairOutputPSP(),"is_pair")

type ListRefOutputPSP <: OutputPSP end
simulate(psp::ListRefOutputPSP,args::OutputArgs) = length(args.operandValues[1],args.operandValues[2]+1)
builtInSPs[symbol("list_ref")] = SP(NullRequestPSP(),ListRefOutputPSP(),"list_ref")


#    {"map_list", new MapListSP},

############################### Map 
type MakeMapOutputPSP <: OutputPSP end
function simulate(psp::MakeMapOutputPSP,args::OutputArgs)
  m = [key => val for (key,val) in zip(args.operandValues...)]
  println(string("constructed map: ",m))
  return m
end
builtInSPs[symbol("make_map")] = SP(NullRequestPSP(),MakeMapOutputPSP(),"make_map")

    
######################## Array
type MakeArrayOutputPSP <: OutputPSP end
simulate(psp::MakeArrayOutputPSP,args::OutputArgs) = args.operandValues
builtInSPs[symbol("make_vector")] = SP(NullRequestPSP(),MakeArrayOutputPSP(),"make_vector")
