#!/bin/bash

if [ "$#" -ne 2 ]; then
	echo "Usage: $0 <docker_container_name_or_id> <path_to_directory>"
	exit 1
fi

CONTAINER_NAME_OR_ID=$1
DIRECTORY_PATH=$2

FILE_COUNT=$(docker exec $CONTAINER_NAME_OR_ID sh -c "find $DIRECTORY_PATH -maxdepth 1 -type f | wc -l")

echo $FILE_COUNT

exit $FILE_COUNT
