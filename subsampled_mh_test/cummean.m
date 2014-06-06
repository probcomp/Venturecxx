function m = cummean(x, dim)

if ~exist('dim','var') || isempty(dim)
  dim = find(size(x) ~= 1, 1);
  if isempty(dim)
    return 
  end
end

s = cumsum(x, dim);
sz = ones(1, ndims(x));
sz(dim) = size(x, dim);
m = bsxfun(@rdivide, s, reshape(1:size(x,dim), sz));

end