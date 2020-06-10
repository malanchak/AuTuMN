#!/bin/bash
set -e
ls -la
echo "Installing AWS CLI script requirements."
echo "Creating virtualenv"
ls -la
ls -la venv
pip install virtualenv
virtualenv venv
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
