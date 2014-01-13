function cartesianProduct(xs::Array)
  @assert !isempty(xs)
  if length(xs) == 1
    return xs[1]::Array
  elseif length(xs) == 2
    z = Array(Any,length(xs[1]::Array) * length(xs[2]::Array))
    for i = 1:length(xs[1])
      for j = 1:length(xs[2])
        k = (j-1) * length(xs[1]) + i
        z[k] = {xs[1][i],xs[2][j]}
      end
    end
    return z
  else
    rest = cartesianProduct(xs[2:end])
    all = [ [[{u},v] for v in rest] for u in xs[1]]
    return reduce(vcat,all)
  end
end

normalizeList(seq) = normalizeList(seq,sum(seq))
function normalizeList(seq,N)
  if N > 0
    return [x/N for x in seq]
  else
    return [0 for x in seq]
  end
end
