load data/output/jointdplr/stage_jointdplr_test_circle_mh.mat

T = length(ts);

if iscell(ws(1))
  maxZ = 0;
  for i = 1 : T
    ws{i} = double(ws{i});
    zCounts{i} = double(zCounts{i});
    maxZ = max(maxZ, max(zCounts{i}(:,1)));
    
    zs = zeros(maxZ, T);
    for i = 1 : T
      zs(zCounts{i}(:,1),i) = zCounts{i}(:,2);
    end
    
    t_int = zeros(maxZ, 2);
    for i = 1 : maxZ
      ii = find(zs(i,:) ~= 0, 1, 'first');
      if ~isempty(ii)
        t_int(i,1) = ii;
        ii = find(zs(i,:) ~= 0, 1, 'last');
        t_int(i,2) = ii;
        assert(all(zs(i,t_int(i,1):t_int(i,2)) ~= 0))
      end
    end
    figure(1)
    for i = 1:maxZ
      if t_int(i,1) ~= 0
        plot(t_int(i,:), i * [1, 1], '-'); hold on
      end
    end
    hold off
  end
else
  zCounts = double(zCounts);
  maxZ = max(max(zCounts(:, :, 1), [], 1), [], 2);
end

ld = load('data/input/circle_data.mat');
acc = mean(bsxfun(@eq, ys_pred, ld.Ytst), 2);

plot(acc)








