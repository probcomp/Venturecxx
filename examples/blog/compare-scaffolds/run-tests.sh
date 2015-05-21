profile_with_filter () {
    outfile="sets-with-filter.txt"
    if [ -e $outfile ]
    then
        rm $outfile
    fi
    for set_model in filter_n filter_n_predict filter_n_thunk
    do
        echo "Running tests for $set_model" >> $outfile
        venture lite -P -L plugins.py -f compare_scaffolds.vnt \
                -e "[infer (test_sets_with_filter $set_model)]" >> $outfile
    done
}

main () {
    if [ "$1" == "profile_with_filter" ]
    then
        profile_with_filter
    fi
}

main "$1"

