#!/bin/bash
set -e
ls -la
pip install virtualenv
virtualenv venv
. venv/bin/activate
pip install -r autumn-repo/scripts/aws/infra/requirements.txt
deactivate
