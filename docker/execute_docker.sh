#!/bin/bash

if [ "$#" -ne 3 ]; then
	echo "Usage: $0 <container_id> <taskID> <userID>"
	exit 1
fi

CONTAINER_ID="$1"
TASKID="$2"
USERID="$3"

echo "Executing command in the Docker container..."
sudo docker exec $CONTAINER_ID /bin/bash -c "bash /home/run.sh"
if [ $? -ne 0 ]; then
	echo "Error executing command in the container."
	exit 1
fi
echo "Command executed successfully."

echo "Copying the result from the Docker container..."
sudo docker cp $CONTAINER_ID:/home/result/ /data/$TASKID/$USERID/
echo "Result copied to /data/$TASKID/$USERID/"

echo "Stopping and removing the Docker container..."
sudo docker stop $CONTAINER_ID
sudo docker rm $CONTAINER_ID
echo "Container stopped and removed."

echo "Removing the Docker image..."
DOCKER_ID=$(sudo docker ps -a -q --filter "id=$CONTAINER_ID" --format "{{.Image}}")
sudo docker rmi $DOCKER_ID
echo "Image removed."
