#!/bin/bash

set -e

# Variables
REGISTRY="vikasy"
IMAGE_NAME="hirethon-base"
VERSION="${TAG:-latest}"
echo "VERSION: $VERSION"

# Build the guardnine-base Docker image
echo "Building hirethon-base Docker image..."
docker build -t $IMAGE_NAME -f Dockerfile.base .

# Tag with registry and version
TAGGED_IMAGE="$REGISTRY/$IMAGE_NAME:$VERSION"
TAGGED_IMAGE_LATEST="$REGISTRY/$IMAGE_NAME:latest"

echo "Tagging image: $IMAGE_NAME -> $TAGGED_IMAGE"
docker tag $IMAGE_NAME $TAGGED_IMAGE

echo "Tagging image: $IMAGE_NAME -> $TAGGED_IMAGE_LATEST"
docker tag $IMAGE_NAME $TAGGED_IMAGE_LATEST

echo "hirethon-base image has been successfully built, tagged, and is ready for use!"
