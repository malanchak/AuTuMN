#!/bin/bash
set -e
ls venv/bin
exit 1
cp -r venv autumn-repo/scripts/aws/env
ls autumn-repo/scripts/aws
ls autumn-repo/scripts/aws/env
echo "this is new"
autumn-repo/scripts/aws/run.sh status
