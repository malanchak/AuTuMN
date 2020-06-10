#!/bin/bash
echo "Installing AWS CLI script requirements."
if [ ! -d "venv" ]
then
    echo "No virtualenv found - creating a new one."
    pip install virtualenv
    virtualenv venv
else
    echo "Already found virtualenv."
fi
echo "Installing requirements"
. venv/bin/activate
pip install -r autumn-repo/scripts/aws/infra/requirements.txt
deactivate
