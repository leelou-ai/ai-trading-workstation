#!/usr/bin/env bash
set -e

CONTAINER_NAME="finally-app"
IMAGE_NAME="finally"
PORT=8000

# Parse flags
BUILD=false
for arg in "$@"; do
  case $arg in
    --build|-b) BUILD=true ;;
  esac
done

# Check Docker is available and running
if ! command -v docker &>/dev/null; then
  echo "Error: Docker is not installed. Install Docker Desktop from https://www.docker.com/products/docker-desktop/"
  exit 1
fi
if ! docker info &>/dev/null; then
  echo "Error: Docker daemon is not running. Please start Docker Desktop and try again."
  exit 1
fi

# Check for .env file
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    echo "No .env file found. Copying from .env.example..."
    cp .env.example .env
    echo "Please edit .env and add your OPENROUTER_API_KEY"
  else
    echo "No .env file found. Creating minimal .env..."
    echo "OPENROUTER_API_KEY=" > .env
  fi
fi

# Stop existing container if running
if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
  echo "Stopping existing container..."
  docker stop $CONTAINER_NAME >/dev/null
fi
if docker ps -aq -f name=$CONTAINER_NAME | grep -q .; then
  docker rm $CONTAINER_NAME >/dev/null
fi

# Build image if needed
if [ "$BUILD" = true ] || ! docker images -q $IMAGE_NAME | grep -q .; then
  echo "Building Docker image..."
  docker build -t $IMAGE_NAME .
fi

# Run the container
echo "Starting FinAlly..."
docker run -d \
  --name $CONTAINER_NAME \
  -p $PORT:8000 \
  -v finally-data:/app/db \
  --env-file .env \
  $IMAGE_NAME

echo ""
echo "FinAlly is running\!"
echo "   Open: http://localhost:$PORT"
echo ""
echo "   To stop:      ./scripts/stop_mac.sh"
echo "   To view logs: docker logs -f $CONTAINER_NAME"
