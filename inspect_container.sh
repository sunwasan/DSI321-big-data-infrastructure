#!/bin/bash
# This script will help inspect the Docker container's internal structure

# Get the container ID
CONTAINER_ID=$(docker ps | grep streamlit | awk '{print $1}')

if [ -z "$CONTAINER_ID" ]; then
  echo "Streamlit container not running"
  exit 1
fi

echo "Streamlit container ID: $CONTAINER_ID"

echo "==== Showing directory structure ===="
docker exec $CONTAINER_ID sh -c "ls -la /frontend"
docker exec $CONTAINER_ID sh -c "ls -la /data"
docker exec $CONTAINER_ID sh -c "ls -la /src"
docker exec $CONTAINER_ID sh -c "ls -la /src/config"

echo "==== Checking if FAQ directory exists ===="
docker exec $CONTAINER_ID sh -c "ls -la /data/faq"

echo "==== Checking if font file exists ===="
docker exec $CONTAINER_ID sh -c "find / -name 'Sarabun-Regular.ttf' 2>/dev/null"

echo "==== Viewing environment variables ===="
docker exec $CONTAINER_ID sh -c "env | sort"
