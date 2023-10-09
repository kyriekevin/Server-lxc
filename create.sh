#!/bin/bash

LOGFILE="./container_creation.log"

log_message() {
	local level=$1
	shift
	local message="$@"
	echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$level] $message" | tee -a $LOGFILE
}

SSH_START_PORT=2222

for i in {1..4}; do
	CONTAINER_NAME="vm$i"
	if lxc list | grep -q $CONTAINER_NAME; then
		log_message "ERROR" "Container $CONTAINER_NAME already exists!"
		exit 1
	fi

	log_message "INFO" "Launching container $CONTAINER_NAME..."
	lxc launch images:ubuntu/focal/amd64 $CONTAINER_NAME >>$LOGFILE 2>&1 || {
		log_message "ERROR" "Failed to launch $CONTAINER_NAME"
		exit 1
	}

	log_message "INFO" "Mapping SSH port for $CONTAINER_NAME to port $SSH_START_PORT on host."
	lxc config device add $CONTAINER_NAME sshport$SSH_START_PORT proxy listen=tcp:0.0.0.0:$SSH_START_PORT connect=tcp:127.0.0.1:22 || {
		log_message "ERROR" "Error setting SSH port for $CONTAINER_NAME"
		exit 1
	}

	((SSH_START_PORT++))
done

log_message "INFO" "All containers successfully created and configured!"
