profile_unknown_size () {
    outfile="sets-unknown-size.txt"
    if [ -e $outfile ]
    then
        rm $outfile
    fi
    for set_model in unknown_n unknown_n_predict unknown_n_thunk
    do
        echo "Running tests for $set_model" >> $outfile
        venture lite -P -L plugins.py -f sets_unknown_size.vnt \
                -e "[infer (run_test $set_model)]" >> $outfile
    done
}

main () {
    if [ "$1" == "profile_unknown_size" ]
    then
        profile_unknown_size
    fi
}

main "$1"

