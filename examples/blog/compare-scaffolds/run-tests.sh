#!/bin/bash

run_filter () {
    # Whether we use thunks and predict
    for settings in "false,false" "false,true" "true,false"            
    do
        use_thunks=$(echo $settings | cut -f1 -d,)
        predict=$(echo $settings | cut -f2 -d,)
        for i in 5 # 10 15 20 25 30
        do
            echo $i
            venture lite -P -L plugins.py -f compare_scaffolds.vnt \
                    -e "[infer (run_experiment (list 'filter_set $use_thunks $predict true $i))]" \
                    # > "results/filter-thunks-$use_thunks-predict-$predict-$i.txt"
        done
    done
}

run_prefix_k () {
    # Whether we use thunks and predict
    for settings in "false,false" "false,true" "true,false"            
    do
        use_thunks=$(echo $settings | cut -f1 -d,)
        predict=$(echo $settings | cut -f2 -d,)
        for i in 5 10 15 20 25 30
        do
            echo $i
            venture lite -P -L plugins.py -f compare_scaffolds.vnt \
                    -e "[infer (run_experiment (list 'prefix_k $use_thunks $predict true $i))]" \
                    > "results/prefix_k-thunks-$use_thunks-predict-$predict-$i.txt"
        done
    done
}

run_map () {
    # Whether we use thunks and predict
    for settings in "false,false" "false,true" "true,false"            
    do
        use_thunks=$(echo $settings | cut -f1 -d,)
        predict=$(echo $settings | cut -f2 -d,)
        for i in 5 10 15 20 25 30
        do
            echo $i
            venture lite -P -L plugins.py -f compare_scaffolds.vnt \
                    -e "[infer (run_experiment (list 'map_set $use_thunks $predict false $i))]" \
                    > "results/map-thunks-$use_thunks-predict-$predict-$i.txt"
        done
    done
}

main () {
    if [ "$1" == "run_filter" ]
    then
        run_filter
    elif [ "$1" == "run_prefix_k" ]
    then
        run_prefix_k
    elif [ "$1" == "run_map" ]
    then
        run_map
    else
        echo "Bad argument passed"
    fi   
}

main $1
