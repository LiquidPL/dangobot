#!/bin/sh

cd "${0%/*}"

echo "BUILD_VERSION=$(git log -1 --pretty=%h)" >> ../.env
echo "BUILD_DATE=$(date -Iseconds)" >> ../.env
