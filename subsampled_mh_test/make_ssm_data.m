function [X, h, a, sig] = make_ssm_data

% rng('default')

N = 1e4;

al_sig = 1;
bt_sig = 100;

sig_noise = 0.05;

b = 1.1;

a = rand;
% sig = gamrnd(al_sig, 1 / bt_sig);
sig = 0.02;

h = zeros(N, 1);
h(1) = 0;
for n = 2 : N
  h(n) = min((h(n-1) + 1) / (a + 1), (h(n-1) - b) / (a - b)) + randn * sig;
end
X = randn(size(h)) * sig_noise + h.^2;

display(a)
display(sig)

figure(1)
plot(1 : N, h, 'x')

figure(2)
plot(1 : N, X - h.^2, 'x', 1 : N, h.^2, 'x')

figure(3)
%plot(h(1:end-1),h(2:end),'x',[-1, a], [0, 1], [b, a], [0, 1]);
plot(sqrt(max(0,X(1:end-1))), sqrt(max(0,X(2:end))), 'x', h(1:end-1), h(2:end), 'gx',[-1, a], [0, 1], [b, a], [0, 1])

end