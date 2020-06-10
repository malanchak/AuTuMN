#!/bin/bash
# Update all the concourse pipelines
TARGET=autumn
. ./envars.secret.sh

fly -t $TARGET sp \
    -c pipelines/pipeline.yml \
    -v aws_secret_access_key=$AWS_SECRET_ACCESS_KEY \
    -v aws_access_key_id=$AWS_ACCESS_KEY_ID \
    -p test
