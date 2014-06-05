#!/bin/bash
#epss=(0 0.01 0.05 0.1 0.2 0.3 0.5)
#num_epss=${#epss[@]}
#eps=${epss[idx_eps]}

if [[ $# < 2 ]]; then
  echo "Missing argument: data eps"
  exit 1
fi


data=$1
eps=$2

tag=ssm_${data}_tmp_eps${eps}

cmd="unbuffer python subsampled_ssm.py --data ${data} --eps ${eps} | tee data/output/ssm/logs/${tag}.log"

echo "$cmd"
eval "$cmd"
