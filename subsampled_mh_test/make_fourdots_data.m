function [X, Y, Xtst, Ytst] = make_fourdots_data

rng('default')

N = 1e4;
Ntst = 1e3;
ctrs_p = [1, 1; 1, -1; -1, 1; -1, -1]';
ctrs_n = ctrs_p * .8;
sig = 0.1;

[X, Y] = make_data(N, ctrs_p, ctrs_n, sig);
[Xtst, Ytst] = make_data(Ntst, ctrs_p, ctrs_n, sig);

figure(1)
plot(X(1,Y==1), X(2,Y==1), 'gx', X(1,Y==0), X(2,Y==0), 'rx');

figure(2)
plot(Xtst(1,Ytst==1), Xtst(2,Ytst==1), 'gx', Xtst(1,Ytst==0), Xtst(2,Ytst==0), 'rx');

end

function [X, Y] = make_data(N, ctrs_p, ctrs_n, sig)

  Np = round(N / 2);
  Nn = N - Np;
  
  ip = randi(4, 1, Np);
  in = randi(4, 1, Nn);
  
  Xp = zeros(2, Np);
  Xn = zeros(2, Np);
  for i = 1 : 4
    ip0 = find(ip == i);
    N0 = length(ip0);
    Xp(:, ip0) = [randn(1, N0) * sig + 1.5; randn(1, N0) * sig * 2];
    theta = i * pi / 2 - pi / 4;
    Xp(:, ip0) = [cos(theta), -sin(theta); sin(theta), cos(theta)] * Xp(:, ip0);
    
    in0 = find(in == i);
    N0 = length(in0);
    Xn(:, in0) = [randn(1, N0) * sig + 1.5 + 0.3; randn(1, N0) * sig * 2];
    theta = i * pi / 2 - pi / 4;
    Xn(:, in0) = [cos(theta), -sin(theta); sin(theta), cos(theta)] * Xn(:, in0);
  end
  X = [Xp, Xn];
  
%   X = [ctrs_p(:, ip), ctrs_n(:, in)];
%   X = X + randn(2, N) * sig;
  Y = [ones(1, Np), zeros(1, Nn)];

  rand_idx = randperm(N);
  X = X(:, rand_idx);
  Y = Y(:, rand_idx);

end