function risk = bayeslr_risk(X, Ws, p_gt)

N = size(X, 2);
T = size(Ws, 2);

risk = zeros(T, 1);

stride = 100;
for i = 1 : stride : N

  is = i : min(i + stride - 1, N);
  
  x = X(:, is);
  p_pred = bsxfun(@rdivide, cumsum(1 ./ (1 + exp(-(x' * Ws))), 2), 1 : T);
  risk = risk + sum((bsxfun(@minus, p_pred, p_gt(is)).^2), 1)';
end
risk = risk / N;

end
  