#!/bin/bash
echo "Installing virtualenv"
pip install virtualenv

echo "Creating virtualenv"
virtualenv venv
. venv/bin/activate
pip install -r autumn-repo/scripts/aws/infra/requirements.txt
deactivate

echo "Testing virtualenv copy"
cp -r venv autumn-repo/scripts/aws/env
echo "Testing virtualenv on script"
autumn-repo/scripts/aws/run.sh
