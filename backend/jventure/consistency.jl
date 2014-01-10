function assertTorus(scaffold::Scaffold)
  for (node,regenCount) = scaffold.regenCounts 
    if regenCount != 0
      print(regenCount)
    end
    @assert regenCount == 0
  end
end

function assertTrace(trace)
  for (id,root) = trace.families
    checkFamily(trace,root)
  end

  for (node,sprecord) = trace.madeSPRecords
    @assert isa(getValue(trace,node),SPRef)
    for (fid,root) = sprecord.families
      checkFamily(trace,root)
    end
  end
end

function checkFamily(trace,root)
  @assert root.valid
  @assert getValue(trace,root) != nothing
  if isa(getValue(trace,root),SPRef) && getValue(trace,root).makerNode == root
    @assert haskey(trace.madeSPRecords,root)
  end

  if isa(root,OutputNode)
    @assert root.requestNode.valid
    @assert getValue(trace,root.requestNode) != nothing
    @assert isa(getValue(trace,root.requestNode),Request)
    checkFamily(trace,getOperatorNode(trace,root))
    for operandNode = getOperandNodes(trace,root)
      checkFamily(trace,operandNode)
    end
  end
end
