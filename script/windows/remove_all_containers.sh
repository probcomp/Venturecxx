boot2docker ssh '
echo "Stopping all containers..."
docker rm -f $(docker ps -a -q)
echo "Press enter to continue... "
read -n1 -s
'