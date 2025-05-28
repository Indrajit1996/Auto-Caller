#!/bin/bash
set -e

if [[ -f ".env" ]]; then
    set -a && source .env && set +a
    echo ".env file loaded successfully."
else
    echo ".env file not found, creating .env from .env.example."
    cp .env.example .env
fi

PROJECT_NAME=$STACK_NAME
RELEASE_VERSION=$VERSION
GITHUB_REGISTRY="ghcr.io"
ORGANIZATION_NAME="dtnetwork"
PROJECT_REGISTRY=$GITHUB_REGISTRY/$ORGANIZATION_NAME/$PROJECT_NAME
IMAGE_NAME=$PROJECT_NAME\-backend

check_deployment() {
    if ! docker ps -a | grep -q $IMAGE_NAME; then
        echo "No container with name $IMAGE_NAME found. App is not currently deployed."
        echo "Run the deployment and then trigger the release action."
        exit 1
    fi
}

#check if the app is up
check_deployment
# login to the container registry
docker login -u=$USERNAME -p=$PASSWORD $GITHUB_REGISTRY
# tag the image with the required version
docker image tag $IMAGE_NAME $PROJECT_REGISTRY/$IMAGE_NAME:$RELEASE_VERSION
# also tag it as 'latest'
docker image tag $IMAGE_NAME $PROJECT_REGISTRY/$IMAGE_NAME:latest
# push the image to container registry
docker push $PROJECT_REGISTRY/$IMAGE_NAME --all-tags
