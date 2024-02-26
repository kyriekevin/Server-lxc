#!/bin/bash

if [ "$#" -ne 3 ]; then
	echo "Usage: $0 <docker_container_name_or_id> <taskID> <userID>"
	exit 1
fi

CONTAINER_NAME_OR_ID=$1
TASK_ID=$2
USER_ID=$3

FILE_COUNT=$(docker exec $CONTAINER_NAME_OR_ID sh -c "ls /home/result | wc -l")
TOTAL_FILE_COUNT=$(ls eval_data/images | wc -l)

if [ "$TOTAL_FILE_COUNT" -ne 0 ]; then
	PERCENTAGE=$(echo "scale=2; $FILE_COUNT / $TOTAL_FILE_COUNT * 100" | bc)
else
	PERCENTAGE=0
fi

echo "$PERCENTAGE" >/data/$TASK_ID/$USER_ID/percentage.txt
