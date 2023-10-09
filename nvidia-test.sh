#!/bin/bash

LOGFILE="./container_creation.log"

log_message() {
    local level=$1
    shift
    local message="$@"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$level] $message" | tee -a $LOGFILE
}

# 容器设置
CONTAINER_NAME="vm1"
MEMORY="32GB"
GPU_PCI_ADDRESS="4f:00.0"
SSH_PORT=2222
CPUSET="0-1"

# 创建和配置容器
log_message "INFO" "Launching container $CONTAINER_NAME..."
lxc launch images:ubuntu/focal/amd64 $CONTAINER_NAME
lxc config set $CONTAINER_NAME limits.cpu $CPUSET
lxc config set $CONTAINER_NAME limits.memory $MEMORY
lxc config device add $CONTAINER_NAME gpu gpu pci=$GPU_PCI_ADDRESS
lxc config device add $CONTAINER_NAME sshport proxy listen=tcp:0.0.0.0:$SSH_PORT connect=tcp:127.0.0.1:22

# 配置NVIDIA
lxc config set $CONTAINER_NAME nvidia.runtime true
lxc config set $CONTAINER_NAME nvidia.driver.capabilities all
lxc config device add $CONTAINER_NAME nvidia-libs disk path=/usr/lib/x86_64-linux-gnu/host-nvidia source=/usr/lib/x86_64-linux-gnu/

# 在容器内部安装NVIDIA驱动
lxc exec $CONTAINER_NAME -- apt update
lxc exec $CONTAINER_NAME -- apt install -y software-properties-common
lxc exec $CONTAINER_NAME -- add-apt-repository ppa:graphics-drivers/ppa
lxc exec $CONTAINER_NAME -- apt update
lxc exec $CONTAINER_NAME -- apt install -y nvidia-driver-525
lxc exec $CONTAINER_NAME -- bash -c "echo 'export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:/usr/lib/x86_64-linux-gnu/host-nvidia' >> /etc/bash.bashrc"

# 重启容器以应用更改
lxc restart $CONTAINER_NAME

# 验证
sleep 10  # 等待容器完全启动
lxc exec $CONTAINER_NAME -- nvidia-smi -L

log_message "INFO" "All operations completed!"

