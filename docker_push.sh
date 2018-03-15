#!/bin/bash

docker login -u "$DOCKER_USERNAME" -p "$DOCKER_PASSWORD"
docker tag dangobot "liquidpl/dangobot:latest"
docker push liquidpl/dangobot:latest
