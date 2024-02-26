#!/bin/bash

if [ "$#" -ne 5 ]; then
	echo "Usage: $0 <path_to_tar_file> <gpu_id> <cpu_cores> <taskID> <userID> <memory_limit>"
	exit 1
fi

TAR_PATH="$1"
GPU_ID="$2"
CPU_CORES="$3"
TASKID="$4"
USERID="$5"
MEMORY_LIMIT_GB="$6"
MEMORY_LIMIT="${MEMORY_LIMIT_GB}g"

if [ ! -f "$TAR_PATH" ]; then
	echo "Error: File not found!"
	exit 1
fi

echo "Loading Docker image from $TAR_PATH..."
DOCKER_ID=$(docker load -i $TAR_PATH | awk '{print $3}')
echo "Image loaded with ID: $DOCKER_ID"

echo "Starting the Docker container with mounted path /home/eval_data..."
CONTAINER_ID=$(docker run -d --gpus "\"device=$GPU_ID\"" --cpuset-cpus="$CPU_CORES" -m "$MEMORY_LIMIT" -v /data/$TASKID/eval_data/images:/home/eval_data $DOCKER_ID tail -f /dev/null)

if [ -z "$CONTAINER_ID" ]; then
	echo "Failed to start the Docker container."
	exit 1
fi
echo "Container started with ID: $CONTAINER_ID"

echo "$CONTAINER_ID" >"/data/$TASKID/$USERID/docker_id.txt"
