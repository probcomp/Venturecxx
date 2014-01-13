abstract Node
typealias NodeID Symbol

require("env.jl")
require("value.jl")

type ConstantNode <: Node
  value::VentureValue
  numRequests::Int
  valid::Bool
end

ConstantNode(value::VentureValue) = ConstantNode(value,0,true)

type LookupNode <: Node
  sourceNode::Node
  value::VentureValue
  numRequests::Int
  valid::Bool
end

LookupNode(sourceNode::Node) = LookupNode(sourceNode,sourceNode.value,0,true)

abstract ApplicationNode <: Node

type RequestNode <: ApplicationNode
  operatorNode::Node
  operandNodes::Array{Node}
  env::ExtendedEnvironment
  value::Union(Request,Nothing)
  numRequests::Int
  valid::Bool
end

RequestNode(operatorNode::Node,operandNodes::Array{Node},env::ExtendedEnvironment) = RequestNode(operatorNode,operandNodes,env,Request((ESR)[]),0,false)

type OutputNode <: ApplicationNode
  requestNode::RequestNode
  env::ExtendedEnvironment
  esrParents::Array{Node}
  value::VentureValue
  numRequests::Int
  valid::Bool
end


OutputNode(requestNode::RequestNode) = OutputNode(requestNode,requestNode.env,Array(Node,0),nothing,0,false)


### Printing
import Base.print
import Base.show
Base.print(node::Node) = print("<node>")
Base.show(io::IO,node::Node) = show("<node>")
Base.show(node::Node) = show("<node>")
Base.showcompact(node::Node) = show("<node>")
