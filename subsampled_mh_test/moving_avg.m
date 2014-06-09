function y = moving_avg(x, L)

y = conv(x(:), ones(L, 1), 'valid') / L;