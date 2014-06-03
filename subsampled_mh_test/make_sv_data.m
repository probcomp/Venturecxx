function [X, h, mu, phi, sig] = make_sv_data

% rng('default')

N = 1e4;

std_mu = 0.1;
a_phi = 100;
b_phi = 1;
al_sig = 1;
bt_sig = 100;

mu = randn * std_mu;
phi = betarnd(a_phi, b_phi);
sig = gamrnd(al_sig, 1 / bt_sig);

h = zeros(N, 1);
h(1) = randn * sig + mu;
for n = 2 : N
  h(n) = mu + phi * (h(n-1) - mu) + randn * sig;
end
X = randn(size(h)) .* exp(h / 2);

display(mu)
display(phi)
display(sig)

figure(1)
plot(1 : N, exp(h), 'bx', 1 : N, X.^2, 'gx')

figure(2)
plot(1 : N, h)

end