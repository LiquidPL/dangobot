#!/bin/bash

docker login -u "$DOCKER_USERNAME" -p "$DOCKER_PASSWORD"
docker tag dangobot "liquidpl/dangobot:latest"
docker tag dangobot "liquidpl/dangobot:$(git log -1 --pretty=%h)"
docker push liquidpl/dangobot
