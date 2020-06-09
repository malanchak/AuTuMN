#!/bin/bash
cp -r autumn-repo autumn-env
cd autumn-env
pip install virtualenv
virtualenv env
. env/bin/activate
pip install -r ./scripts/aws/infra/requirements.txt
./scripts/aws/run.sh
