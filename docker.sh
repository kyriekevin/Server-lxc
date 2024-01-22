#!/bin/bash

if [ "$#" -ne 6 ]; then
	echo "Usage: $0 <path_to_tar_file> <gpu_id> <cpu_cores> <mount_path> <taskID> <userID>"
	exit 1
fi

TAR_PATH="$1"
GPU_ID="$2"
CPU_CORES="$3"
MOUNT_PATH="$4"
TASKID="$5"
USERID="$6"

if [ ! -f "$TAR_PATH" ]; then
	echo "Error: File not found!"
	exit 1
fi

echo "Loading Docker image from $TAR_PATH..."
IMAGE_ID=$(sudo docker load -i $TAR_PATH | awk '{print $3}')
echo "Image loaded with ID: $IMAGE_ID"

echo "Starting the Docker container with mounted path $MOUNT_PATH..."
sudo docker run -d --gpus "\"device=$GPU_ID\"" --cpuset-cpus="$CPU_CORES" -m 32g -v /data/$TASKID/eval_data/images:$MOUNT_PATH $IMAGE_ID tail -f /dev/null

if [ $? -ne 0 ]; then
	echo "Failed to start the Docker container."
	exit 1
fi

CONTAINER_ID=$(sudo docker ps -l -q)

if [ -z "$CONTAINER_ID" ]; then
	echo "Failed to retrieve the container ID."
	exit 1
fi
echo "Container started with ID: $CONTAINER_ID"

echo "Executing command in the Docker container..."
sudo docker exec $CONTAINER_ID /bin/bash -c "bash /home/run.sh"
if [ $? -ne 0 ]; then
	echo "Error executing command in the container."
	exit 1
fi
echo "Command executed successfully."

echo "Copying the result from the Docker container..."
mkdir -p /data/$TASKID/
sudo docker cp $CONTAINER_ID:/home/result /data/$TASKID/$USERID/
echo "Result copied to /data/$TASKID/$USERID/"

echo "Stopping and removing the Docker container..."
sudo docker stop $CONTAINER_ID
sudo docker rm $CONTAINER_ID
echo "Container stopped and removed."

echo "Removing the Docker image..."
sudo docker rmi $IMAGE_ID
echo "Image removed."
