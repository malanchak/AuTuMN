#!/bin/bash
echo "Installing virtualenv"
pip install virtualenv

echo "Creating virtualenv"
virtualenv venv
. venv/bin/activate
pip install -r autumn-repo/scripts/aws/infra/requirements.txt
deactivate
