% function postprocess_ssm

% Load data.
% load data/input/mnist_D50_7_9.mat Xtst_pca
% X = Xtst_pca; clear Xtst_pca

% Load results.

% Used in the submission.

% % Results with N=1000.
% epss = [0, 0.001, 0.005, 0.01, 0.05 0.1, 0.3];
% rst_file_prefix = 'data/output/ssm/stage_ssm_init_ssm3_N1000';
% Nepss = length(epss);
% digit = 3;

% Results with N=1000.
epss = [0, 0.005, 0.01, 0.02, 0.05, 0.1, 0.3];
% epss = [0, 0.01, 0.05, 0.1, 0.3];
rst_file_prefix = 'data/output/ssm/stage_ssm_ssm4_N10000';
Nepss = length(epss);
digit = 2;

% % Not used in the submission.
% 
% % epss = [0, 0.01, 0.05, 0.1, 0.2];
% % rst_file_prefix = 'data/output/ssm/stage_ssm_L10Loop_ssm3_N1000';
% % Nepss = length(epss);
% % digit = 2;
% 
% % epss = [0, 0.001, 0.005, 0.01, 0.05 0.1, 0.3];
% % rst_file_prefix = 'data/output/ssm/stage_ssm_init_ssm4_N10000';
% % Nepss = length(epss);
% % digit = 3;

fprintf('Loading results...\n')
for i = 1 : Nepss
  if epss(i) == 0
    rst_file = [rst_file_prefix, '_mh.mat'];
  elseif epss(i) < 0.01 || digit == 3
    rst_file = sprintf('%s_submh_%.3f.mat', rst_file_prefix, epss(i));
  else
    rst_file = sprintf('%s_submh_%.2f.mat', rst_file_prefix, epss(i));
  end
  rsts(i) = load(rst_file, 'ts', 'ts_sampa', 'ts_samph', 'a', 'sig', 'h');
end

% Plot Risk.
% figure
% cm = hsv(Nepss);
% legend_str = cell(Nepss, 1);
% for i = 1 : Nepss
%   plot(rsts(i).ts, rsts(i).a, 'color', cm(i,:)); hold on
%   legend_str{i} = sprintf('\\epsilon = %.2f, T = %d', epss(i), length(rsts(i).ts));
% end
% hold off
% set(gca, 'fontSize', 14)
% legend(legend_str)
% set(gca, 'fontSize', 20)
% xlabel('Time (second)');
% ylabel('a');


figure
cm = hsv(Nepss);
legend_str = cell(Nepss, 1);
for i = 1 : Nepss
  plot(rsts(i).ts/3600, cummean(rsts(i).a), 'color', cm(i,:)); hold on
  legend_str{i} = sprintf('\\epsilon = %.3f', epss(i));
end
hold off
set(gca, 'fontSize', 14)
legend(legend_str)
set(gca, 'fontSize', 20)
xlabel('Time (hour)');
ylabel('Avg a');


figure
cm = hsv(Nepss);
legend_str = cell(Nepss, 1);
for i = 1 : Nepss
  plot(rsts(i).ts, cummean(rsts(i).sig), 'color', cm(i,:)); hold on
  legend_str{i} = sprintf('\\epsilon = %.3f', epss(i));
end
hold off
set(gca, 'fontSize', 14)
legend(legend_str)
set(gca, 'fontSize', 20)
xlabel('Time (second)');
ylabel('Avg sig');



%%
% 
% i = find(epss == 0.1);
% h = rsts(i).h;
% figure
% for t = 1 : size(h,1)
%   plot(h(t,1:end-1),h(t,2:end),'x')
%   title(t); pause
% end
% 

