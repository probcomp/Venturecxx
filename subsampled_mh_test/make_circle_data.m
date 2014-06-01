function [X, Y, Xtst, Ytst] = make_circle_data

rng('default')

N = 1e4;
Ntst = 1e3;
Rp = 0.5;
Rn = 0.45;
sig = 0.02;

[X, Y] = make_data(N, Rp, Rn, sig);
[Xtst, Ytst] = make_data(Ntst, Rp, Rn, sig);

figure(1)
plot(X(1,Y==1), X(2,Y==1), 'gx', X(1,Y==0), X(2,Y==0), 'rx');

figure(2)
plot(Xtst(1,Ytst==1), Xtst(2,Ytst==1), 'gx', Xtst(1,Ytst==0), Xtst(2,Ytst==0), 'rx');

end

function [X, Y] = make_data(N, Rp, Rn, sig)

  Np = round(N / 2);
  Nn = N - Np;
  
  theta = rand(1, N) * (2 * pi);
  X = [Rp * [cos(theta(1 : Np)); sin(theta(1 : Np))], ...
       Rn * [cos(theta(1 : Np)); sin(theta(1 : Np))]];
  X = X + randn(2, N) * sig;
  Y = [ones(1, Np), zeros(1, Nn)];

  rand_idx = randperm(N);
  X = X(:, rand_idx);
  Y = Y(:, rand_idx);

end