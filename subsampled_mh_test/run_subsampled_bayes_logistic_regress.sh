#!/bin/bash
#epss=(0 0.01 0.05 0.1 0.2 0.3 0.5)
#num_epss=${#epss[@]}
#eps=${epss[idx_eps]}

if [[ $# == 0 ]]; then
  echo "Missing argument: eps"
  exit 1
fi


eps=$1

tag=bayeslr_fast_m100_Time5e5_mnist

cmd="unbuffer python subsampled_bayes_logistic_regress.py --data mnist --eps ${eps} | tee data/output/bayeslr/logs/${tag}_eps${eps}.log"

echo "$cmd"
eval "$cmd"
