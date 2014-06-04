function [X, Y, Xtst, Ytst] = make_quad_data

rng('default')

N = 1e4;
Ntst = 1e3;
offset = 0.2;
sig = 0.05;

[X, Y] = make_data(N, offset, sig);
[Xtst, Ytst] = make_data(Ntst, offset, sig);

figure(1)
plot(X(1,Y==1), X(2,Y==1), 'gx', X(1,Y==0), X(2,Y==0), 'rx');

figure(2)
plot(Xtst(1,Ytst==1), Xtst(2,Ytst==1), 'gx', Xtst(1,Ytst==0), Xtst(2,Ytst==0), 'rx');

end

function [X, Y] = make_data(N, offset, sig)

  Np = round(N / 2);
  Nn = N - Np;
  
  Xp = rand(1, Np) * 2 - 1;
  Xp = [Xp; Xp.^2];
  Xn = rand(1, Nn) * 2 - 1;
  Xn = [Xn; Xn.^2 + offset];

  X = [Xp, Xn];
  X = X + randn(2, Np + Nn) * sig;
  Y = [ones(1, Np), zeros(1, Nn)];

  rand_idx = randperm(N);
  X = X(:, rand_idx);
  Y = Y(:, rand_idx);

end