echo "Stopping, updating, initializing, and restarting boot2docker"
echo "This script only needs to be run once after boot2docker installation"

boot2docker stop
boot2docker download
boot2docker init
boot2docker start

echo 'Press enter to continue...'
read -n1 -s