#!/bin/bash

if [ "$#" -ne 1 ]; then
	echo "Usage: $0 <docker_container_name_or_id> "
	exit 1
fi

CONTAINER_NAME_OR_ID=$1

FILE_COUNT=$(docker exec $CONTAINER_NAME_OR_ID sh -c "ls /home/result | wc -l")
# 获取文件总数
# ls eval_data/images | wc -l

echo $FILE_COUNT

exit $FILE_COUNT
