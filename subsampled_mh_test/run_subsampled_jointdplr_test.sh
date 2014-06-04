#!/bin/bash
#epss=(0 0.01 0.05 0.1 0.2 0.3 0.5)
#num_epss=${#epss[@]}
#eps=${epss[idx_eps]}

if [[ $# == 0 ]]; then
  echo "Missing argument: eps"
  exit 1
fi


eps=$1

tag=jointdplr_test_four_cluster

cmd="unbuffer python subsampled_jointdplr_test.py --data four_cluster --eps ${eps} | tee data/output/jointdplr/logs/${tag}_eps${eps}.log"

echo "$cmd"
eval "$cmd"
