#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <path_to_tar_file> <gpu_id> <cpu_cores>"
    exit 1
fi

TAR_PATH="$1"
GPU_ID="$2"
CPU_CORES="$3"

if [ ! -f "$TAR_PATH" ]; then
    echo "Error: File not found!"
    exit 1
fi

echo "Loading Docker image from $TAR_PATH..."
IMAGE_ID=$(sudo docker load -i $TAR_PATH | awk '{print $3}')
echo "Image loaded with ID: $IMAGE_ID"

echo "Starting the Docker container..."
sudo docker run -d --gpus "\"device=$GPU_ID\"" --cpuset-cpus="$CPU_CORES" -m 32g $IMAGE_ID tail -f /dev/null

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
sudo docker exec $CONTAINER_ID /bin/bash -c "source /root/miniconda3/etc/profile.d/conda.sh && conda activate pytorch && python /root/resnet.py"
if [ $? -ne 0 ]; then
    echo "Error executing command in the container."
    exit 1
fi
echo "Command executed successfully."

echo "Stopping and removing the Docker container..."
sudo docker stop $CONTAINER_ID
sudo docker rm $CONTAINER_ID
echo "Container stopped and removed."

echo "Removing the Docker image..."
sudo docker rmi $IMAGE_ID
echo "Image removed."
