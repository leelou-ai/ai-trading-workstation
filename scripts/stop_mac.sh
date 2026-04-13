#!/usr/bin/env bash

CONTAINER_NAME="finally-app"

if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
  echo "Stopping FinAlly..."
  docker stop $CONTAINER_NAME >/dev/null
  docker rm $CONTAINER_NAME >/dev/null
  echo "FinAlly stopped. (Data volume preserved)"
else
  echo "FinAlly is not running."
fi
