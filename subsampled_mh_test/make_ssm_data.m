function [X, h, a, sig, sig_noise, b] = make_ssm_data(a, sig)

% rng('default')

T = 1e4;
N = 1;

al_sig = 1;
bt_sig = 100;

sig_noise = 0.001; % 0.05;

b = 1.1;

if ~exist('a', 'var') || isempty(a)
  a = rand;
end
if ~exist('sig', 'var') || isempty(sig)
  % sig = gamrnd(al_sig, 1 / bt_sig);
  sig = 0.02;
end

h = zeros(T, N);
for n = 1 : N
  h(1, n) = rand;
  for t = 2 : T
    h(t, n) = min((h(t-1, n) + 1) / (a + 1), (h(t-1, n) - b) / (a - b)) + randn * sig;
  end
end
X = randn(size(h)) * sig_noise + h.^2;

display(a)
display(sig)

figure(1)
plot(1 : T, h(:, 1:min(3,end)), 'x')

figure(2)
plot(1 : T * N, X(:) - h(:).^2, 'x', 1 : T * N, h(:).^2, 'x')

figure(3)
plot(reshape(h(1:end-1,:), (T-1)*N, 1), reshape(h(2:end,:), (T-1)*N, 1), 'x')
%plot(h(1:end-1),h(2:end),'x',[-1, a], [0, 1], [b, a], [0, 1]);

end