boot2docker up
boot2docker ip
boot2docker ssh "
cd $(pwd)
if [ ${PWD##*/} = 'windows' ]; then
    cd ../..
fi

echo 'Visit http://192.168.59.103:8888/ in your browser to see example notebooks'

source script/run_docker_container

echo 'Press enter to continue...'
read -n1 -s
"