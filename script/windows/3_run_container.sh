boot2docker up
boot2docker ip
boot2docker ssh "
cd $(pwd)
if [ ${PWD##*/} = 'windows' ]; then
    cd ../..
fi

echo 'Visit http://192.168.59.103:8888/ in your browser to see example notebooks'

docker run -ti -p 8888:8888 -p 5900:5900 -p 9001:9001 -v \$(pwd):/root/Venturecxx venture 

echo 'Press enter to continue...'
read -n1 -s
"