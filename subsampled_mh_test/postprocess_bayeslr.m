% function postprocess_bayeslr

% Load data.
load data/input/mnist_D50_7_9.mat Xtst_pca
X = Xtst_pca; clear Xtst_pca

% Load and compute ground truth.
load data/input/lr_mnist_pca_hmc_1e5.mat samps
fprintf('Computing the ground truth...\n')
p_gt = bayeslr_predict_gt([X; ones(1, size(X, 2))], samps);
clear samps
X = [ones(1, size(X, 2)); X];

% Load results.
epss = [0, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5];
Nepss = length(epss);
rsts = repmat(struct('ts', [], 'ws', []), Nepss, 1);
rst_file_prefix = 'data/output/bayeslr/stage_bayeslr_fast_m100_Time5e5_mnist';
fprintf('Loading results...\n')
for i = 1 : Nepss
  if epss(i) == 0
    rst_file = [rst_file_prefix, '_mh.mat'];
  else
    rst_file = sprintf('%s_submh_%.2f.mat', rst_file_prefix, epss(i));
  end
  ld = load(rst_file, 'ts', 'ws');
  rsts(i).ts = ld.ts';
  rsts(i).ws = ld.ws';
end

% Compute Risk.
risks = repmat(struct('ts', [], 'risk', []), Nepss, 1);
for i = 1 : Nepss
  fprintf('Computing %d''th risk...\n', i)
  risks(i).ts = rsts(i).ts;
  risks(i).risk = bayeslr_risk(X, rsts(i).ws, p_gt);
end

% Plot Risk.
figure
cm = hsv(length(risks));
legend_str = cell(Nepss, 1);
for i = 1 : Nepss
  plot(risks(i).ts / 3600, log(risks(i).risk), 'color', cm(i,:)); hold on
  legend_str{i} = sprintf('\\epsilon = %.2f, T = %d', epss(i), length(rsts(i).ts));
end
hold off
set(gca, 'fontSize', 14)
legend(legend_str)
set(gca, 'fontSize', 20)
xlabel('Time (hour)');
ylabel('Log (Risk)');

%% Compute prediction 
% p_pred = zeros(size(ld.Ytst));
% for i = 1 : length(ld.Ytst)
%   p_pred(i) = mean(1 ./ (1 + exp(-(ws * [1;ld.Xtst_pca(:,i)]))));
% end


