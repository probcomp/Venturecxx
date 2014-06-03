function p = bayeslr_predict_gt(X, Ws)

N = size(X, 2);
p = zeros(N, 1);

for i = 1 : N
  p(i) = mean(1 ./ (1 + exp(-(X(:, i)' * Ws))));
end

end
  

