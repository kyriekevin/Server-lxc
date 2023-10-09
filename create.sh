#!/bin/bash

LOGFILE="./container_creation.log"

log_message() {
    local level=$1
    shift
    local message="$@"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$level] $message" | tee -a $LOGFILE
}

CPUS="2"
MEMORY="32GB"  # for LXC config
MEMORY_MB=32000  # in MB for the script
GPUS=("4f:00.0" "52:00.0" "56:00.0" "57:00.0") # lspci | grep -i nvidia
SSH_START_PORT=2222
CPU_SETS=("0-1" "2-3" "4-5" "6-7")

# Check CPUs
TOTAL_CPUS=$(nproc)
log_message "INFO" "Detected $TOTAL_CPUS CPUs."
if [ $TOTAL_CPUS -lt 8 ]; then
    log_message "ERROR" "Not enough CPUs. Exiting."
    exit 1
fi

# Check Memory
TOTAL_MEMORY=$(free -m | awk '/^Mem:/{print $2}')
log_message "INFO" "Detected $TOTAL_MEMORY MB of total memory."
if [ $TOTAL_MEMORY -lt $(( 4 * MEMORY_MB )) ]; then
    log_message "ERROR" "Not enough Memory. Exiting."
    exit 1
fi

# Check GPUs
AVAILABLE_GPUS=$(nvidia-smi -L | wc -l)
log_message "INFO" "Detected $AVAILABLE_GPUS GPUs."
if [ $AVAILABLE_GPUS -lt 4 ]; then
    log_message "ERROR" "Not enough GPUs. Exiting."
    exit 1
fi

for i in {1..4}
do
    CONTAINER_NAME="vm$i"
    if lxc list | grep -q $CONTAINER_NAME; then
       log_message "ERROR" "Container $CONTAINER_NAME already exists!"
       exit 1
    fi

    log_message "INFO" "Launching container $CONTAINER_NAME..."
    lxc launch images:ubuntu/focal/amd64 $CONTAINER_NAME >> $LOGFILE 2>&1 || { log_message "ERROR" "Failed to launch $CONTAINER_NAME"; exit 1; }

    CPUSET=${CPU_SETS[$i-1]}
    log_message "INFO" "Setting $CPUS CPUs for $CONTAINER_NAME."
    lxc config set $CONTAINER_NAME limits.cpu $CPUSET || { log_message "ERROR" "Error setting CPU for $CONTAINER_NAME"; exit 1; }

    log_message "INFO" "Setting $MEMORY memory for $CONTAINER_NAME."
    lxc config set $CONTAINER_NAME limits.memory $MEMORY || { log_message "ERROR" "Error setting memory for $CONTAINER_NAME"; exit 1; }

    GPU_PCI_ADDRESS=${GPUS[$i-1]}
    log_message "INFO" "Assigning GPU with address $GPU_PCI_ADDRESS to $CONTAINER_NAME."
    lxc config device add $CONTAINER_NAME gpu$i gpu pci=$GPU_PCI_ADDRESS || { log_message "ERROR" "Error setting GPU for $CONTAINER_NAME"; exit 1; }

    log_message "INFO" "Mapping SSH port for $CONTAINER_NAME to port $SSH_START_PORT on host."
    lxc config device add $CONTAINER_NAME sshport$SSH_START_PORT proxy listen=tcp:0.0.0.0:$SSH_START_PORT connect=tcp:127.0.0.1:22 || { log_message "ERROR" "Error setting SSH port for $CONTAINER_NAME"; exit 1; }

    ((SSH_START_PORT++))
done

log_message "INFO" "All containers successfully created and configured!"
