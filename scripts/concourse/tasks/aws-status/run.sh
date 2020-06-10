#!/bin/bash
set -e
echo "local repo"
ls venv/bin
which python
. venv/bin/activate
which python
deactivate

cp -r venv autumn-repo/scripts/aws/env
echo "autumn repo"
ls autumn-repo/scripts/aws
ls autumn-repo/scripts/aws/env
which python
. autumn-repo/scripts/aws/env/bin/activate
which python
deactivate

#echo "this is new"
#autumn-repo/scripts/aws/run.sh status
