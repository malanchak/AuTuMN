#!/bin/bash
# Update all the concourse pipelines
. ./envars.secret.sh
MODELS="malaysia"
for MODEL in $MODELS
do
    fly -t autumn sp \
        -c pipelines/pipeline.yml \
        -v AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
        -v AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
        -v AWS_SSH_KEY_1="$AWS_SSH_KEY_1" \
        -v AWS_SSH_KEY_2="$AWS_SSH_KEY_2" \
        -v model=$MODEL \
        -p $MODEL
done
