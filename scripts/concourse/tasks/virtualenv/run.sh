#!/bin/bash
echo "Installing virtualenv"
pip install virtualenv

echo "Creating virtualenv"
virtualenv venv
. venv/bin/activate
pip install -r autumn-repo/scripts/aws/infra/requirements.txt

echo "Testing virtualenv"
which python
echo "Testing virtualenv freeze"
pip freeze
echo "Testing virtualenv on script"
autumn-repo/scripts/aws/run.sh
