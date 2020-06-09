#!/bin/bash
# Update all the concourse pipelines
TARGET=autumn
fly -t $TARGET sp -c pipelines/pipeline.yml -p test
