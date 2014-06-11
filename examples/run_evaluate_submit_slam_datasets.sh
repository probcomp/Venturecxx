function create_perl_str_0 {
	echo "'s/^paths.*$/paths = run_slam, filter.py, vehicle_simulator.py, vehicle_program.py, simulator.py, scene_plot_utils.py, contexts.py/; s/^evaluator.*$/evaluator = slam_eval/'"
}

function create_perl_str_1 {
	echo "'s/^input.*$/input = "$1"\/data\/noisy/; s/^ground_truth.*$/ground_truth = "$1"/'"
}

function prep_config_for_slam {
	config_filename=$1
	perl_str=$(create_perl_str_0)
	echo perl -i.bak -pe $perl_str $config_filename | bash
}

function prep_config_for_dataset {
	config_filename=$1
	dataset_name=$2
	perl_str=$(create_perl_str_1 $dataset_name)
	echo perl -i.bak -pe $perl_str $config_filename | bash
}

function run_evaluate_submit {
	config_filename=$1
	dataset_name=$2
	output_name=output_${dataset_name}
	run_id_filename=${dataset_name}_run_id
	#
	prep_config_for_dataset $config_filename $dataset_name
	ppaml run $config_filename -p | \
		tee >(grep ^run_id | awk '{print substr($2, 2)}' > $run_id_filename)
	ppaml evaluate $config_filename $(cat $run_id_filename) -p
	mkdir $output_name
	ppaml submit $output_name $(cat $run_id_filename)
}


config_filename=cps.ini
dataset_names=(1_straight 2_bend 3_curvy 4_circle 5_eight 6_loop 7_random)

prep_config_for_slam $config_filename
for dataset_name in ${dataset_names[*]}; do
	# can't run in parallel, unless each run gets a unique config file
	run_evaluate_submit $config_filename $dataset_name > "${dataset_name}.log"
done

tgz_filenames=
for dataset_name in ${dataset_names[*]};
	do tgz_filenames="$tgz_filenames output_${dataset_name}";
done
tar cvfz mit_ppaml_cp1.tgz $tgz_filenames
