function acc = jointdplr_avg_acc(Ypred, Ytst)

Ytst = Ytst(:);
assert(size(Ypred, 1) == length(Ytst));

acc = mean(bsxfun(@eq, bsxfun(@rdivide, cumsum(Ypred, 2), 1 : size(Ypred, 2)) > 0.5, Ytst));
% acc = mean(bsxfun(@rdivide, cumsum(bsxfun(@eq, Ypred, Ytst), 2)), 1:size(Ypred,2));

end