#!/bin/bash
set -e
ls -la
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
ls -la
ls -la venv
ls -la venv/bin
. venv/bin/activate
which python
which python3
python -V
python3 -V
pip install -r autumn-repo/scripts/aws/infra/requirements.txt
deactivate
