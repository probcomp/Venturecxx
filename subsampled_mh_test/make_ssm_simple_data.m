function [X, h, a, sig] = make_ssm_simple_data

% rng('default')

N = 1e4;

al_sig = 1;
bt_sig = 10;

sig_noise = 0.05;

b = 1.1;

a = rand;
sig = gamrnd(al_sig, 1 / bt_sig);

h = zeros(N, 1);  
h(1) = 0;
for n = 2 : N
  h(n) = min((h(n-1) + 1) / (a + 1), (h(n-1) - b) / (a - b)) + randn * sig;
end
X = randn(size(h)) * sig_noise + h;

display(a)
display(sig)

figure(1)
plot(1 : N, h, 'x')

figure(2)
plot(1 : N, X - h, 'x', 1 : N, h, 'x')

figure(3)
plot(X(1:end-1), X(2:end), 'x', h(1:end-1),h(2:end),'x',[-1, a], [0, 1], [b, a], [0, 1]);

end