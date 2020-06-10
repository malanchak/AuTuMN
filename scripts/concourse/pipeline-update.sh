#!/bin/bash
# Update all the concourse pipelines
. ./envars.secret.sh

fly -t autumn sp \
    -c pipelines/pipeline.yml \
    -v AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    -v AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    -p test
