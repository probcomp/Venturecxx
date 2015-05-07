#! /usr/local/bin/bash

# The reality check tests; pick an inference method

simple_test () {
  result_dir="/Users/dwadden/code/scratch"
  method=$1
  nsamples=$2
  echo $method
  for config in no_observations,0 \
                one_observation_one_color,1 \
                two_observations_same_color,1 \
                two_observations_two_colors,2 \
                two_observations_same_color_noisy,1 \
                two_observations_two_colors_noisy,1 \
                five_observations_two_colors_noisy,1

# for config in no_observations,0

  do
    name=$(echo $config | cut -f1 -d",")
    min_nballs=$(echo $config | cut -f2 -d",")
    echo $name
    basename=${name}_${method}
    if [ $method == "mh" ]
    then
      filename1=${basename}_trace
      filename2=${basename}_hist
      venture lite -P -f poisson_ball.vnt -e \
        "[infer (run_test_$method $name (quote $filename1) (quote $filename2) $nsamples $min_nballs)]"
      mv $filename1.png $filename2.png "$result_dir"
    else
      filename=$basename
      venture lite -P -L poisson_ball_plugin.py -f poisson_ball.vnt -e \
        "[infer (run_test_$method $name (quote $filename) $nsamples $min_nballs)]"
      mv $filename.png "$result_dir"
    fi
  done
}

simple_test rejection 100
simple_test resample 100
simple_test mh 100

################################################################################

# debugging MH with different inference methods
debug_mh() {
  inf_program=$1
  result_dir="/Users/dwadden/Google Drive/probcomp/challenge-problems/problem-4/poisson_mh_debug"
  for n_obs in 1 3 5
  # for n_obs in 1
  do
    for predict_first in "true" "false"
    do
      filename=${inf_program}_${n_obs}_${predict_first}
      venture lite -P -L poisson_ball_plugin.py -f poisson_ball2.vnt -e \
        "[infer (debug_mh $n_obs mh_${inf_program} (quote $filename) $predict_first)]"
      mv $filename.png "$result_dir"
    done
  done
}

# debug_mh one
# debug_mh all
# debug_mh scoped
