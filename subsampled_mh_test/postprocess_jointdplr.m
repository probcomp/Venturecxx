% load data/output/jointdplr/stage_jointdplr_test_circle_mh.mat
% 
% T = length(ts);
% 
% if iscell(ws(1))
%   maxZ = 0;
%   for i = 1 : T
%     ws{i} = double(ws{i});
%     zCounts{i} = double(zCounts{i});
%     maxZ = max(maxZ, max(zCounts{i}(:,1)));
%     
%     zs = zeros(maxZ, T);
%     for i = 1 : T
%       zs(zCounts{i}(:,1),i) = zCounts{i}(:,2);
%     end
%     
%     t_int = zeros(maxZ, 2);
%     for i = 1 : maxZ
%       ii = find(zs(i,:) ~= 0, 1, 'first');
%       if ~isempty(ii)
%         t_int(i,1) = ii;
%         ii = find(zs(i,:) ~= 0, 1, 'last');
%         t_int(i,2) = ii;
%         assert(all(zs(i,t_int(i,1):t_int(i,2)) ~= 0))
%       end
%     end
%     figure(1)
%     for i = 1:maxZ
%       if t_int(i,1) ~= 0
%         plot(t_int(i,:), i * [1, 1], '-'); hold on
%       end
%     end
%     hold off
%   end
% else
%   zCounts = double(zCounts);
%   maxZ = max(max(zCounts(:, :, 1), [], 1), [], 2);
% end
% 
% ld = load('data/input/circle_data.mat');
% acc = mean(bsxfun(@eq, ys_pred, ld.Ytst), 2);
% 
% plot(acc)

% 
% 
% % z = double(zs(end,:));
% z = double(zs(1,:));
% y = Y';
% load data/input/four_cluster_data2.mat
% 
% [uz,~,ic] = unique(z);
% for i = 1:length(uz)
% plot(X(1,ic==i & y==1), X(2,ic==i & y==1), 'gx', X(1,ic==i & y==0), X(2,ic==i & y==0), 'rx'); title([i,sum(ic==i)]); xlim([-2,2]); ylim([-2,2]); pause
% end
% 

%%

load data/input/four_cluster_data2.mat X Xtst Y Ytst

% Load results.
epss = [0, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5];
Nepss = length(epss);
rst_file_prefix = 'data/output/jointdplr/stage_jointdplr_test_four_cluster_N10000';
fprintf('Loading results...\n')
for i = 1 : Nepss
  if epss(i) == 0
    rst_file = [rst_file_prefix, '_mh.mat'];
  else
    rst_file = sprintf('%s_submh_%.2f.mat', rst_file_prefix, epss(i));
  end
  ld = load(rst_file, 'ts', 'zs', 'acc', 'zCounts', 'ys_pred');
  rsts(i).ts = ld.ts;
  rsts(i).zs = double(ld.zs');
  rsts(i).zCounts = ld.zCounts;
  rsts(i).acc = ld.acc';
  rsts(i).ys_pred = double(ld.ys_pred');
  rsts(i).avg_acc = jointdplr_avg_acc(rsts(i).ys_pred, Ytst);
end


% % Plot Accuracy.
% figure
% cm = hsv(length(rsts));
% legend_str = cell(Nepss, 1);
% for i = 1 : Nepss
%   plot(rsts(i).ts(100:100:end), rsts(i).acc, 'color', cm(i,:)); hold on
%   legend_str{i} = sprintf('\\epsilon = %.2f, T = %d', epss(i), length(rsts(i).ts));
%   fprintf('i: %d, tables: %d\n', i, size(rsts(i).zCounts{end},1))
%   pause
% end
% hold off
% % set(gca, 'fontSize', 14)
% legend(legend_str)
% % set(gca, 'fontSize', 20)
% % xlabel('Time (hour)');
% % ylabel('Log (Risk)');

% Plot Accuracy of Averaged Prediction.
figure
cm = hsv(length(rsts));
legend_str = cell(Nepss, 1);
for i = 1 : Nepss
  plot(rsts(i).ts(100:100:end), rsts(i).avg_acc, 'color', cm(i,:)); hold on
%   legend_str{i} = sprintf('\\epsilon = %.2f, T = %d', epss(i), length(rsts(i).ts));
  legend_str{i} = sprintf('\\epsilon = %.2f', epss(i));
  fprintf('i: %d, tables: %d\n', i, size(rsts(i).zCounts{end},1))
%   pause
end
hold off
set(gca, 'fontSize', 14)
legend(legend_str)
set(gca, 'fontSize', 20)
xlabel('Time (second)');
ylabel('Average Accuracy');

% Prediction.
figure
plot(X(1,Y==0), X(2,Y==0), 'rx', X(1,Y==1), X(2,Y==1), 'gx')

i = 6;
figure
Yp = rsts(i).ys_pred(:,end)';
% Yp = mean(rsts(i).ys_pred, 2)' > 0.5;
plot(Xtst(1, Yp == 0 & Ytst == 0), Xtst(2,Yp == 0 & Ytst == 0), 'rx', ...
  Xtst(1, Yp == 1 & Ytst == 1), Xtst(2,  Yp == 1 & Ytst == 1), 'gx', ...
  Xtst(1, Yp == 0 & Ytst == 1), Xtst(2,  Yp == 0 & Ytst == 1), 'kx', ...
  Xtst(1, Yp == 1 & Ytst == 0), Xtst(2,  Yp == 1 & Ytst == 0), 'kx')


%%

d = 3;
w = zeros(length(ws), 3);
for i = 1 : length(ws)
  idx = find(double(zCounts{i}(:,1)) == d);
  w(i,:) = ws{i}(idx,:);
end

