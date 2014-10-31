boot2docker up
boot2docker ssh "
cd $(pwd)
if [ ${PWD##*/} = 'windows' ]; then
    cd ../..
fi
docker run -ti -p 8888:8888 -p 5900:5900 -v \$(pwd):/root/Venturecxx venture

echo 'Press enter to continue...'
read -n1 -s
"