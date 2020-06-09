#!/bin/bash
echo "Installing virtualenv"
pip install virtualenv

echo "Creating virtualenv"
cp -r autumn-repo autumn-env
cd autumn-env
pwd
ls -la
virtualenv env
ls -la
. env/bin/activate
pip install -r ./scripts/aws/infra/requirements.txt
./scripts/aws/run.sh
