#!/bin/bash
set -e
SCRIPT_DIR=$(dirname $0)
pushd $SCRIPT_DIR
if [ ! -d "env" ]
then
    echo "Installing requirements"
    virtualenv -p python3 env
    . env/bin/activate
    pip3 install -r infra/requirements.txt
fi
echo "this works!!!"
. env/bin/activate
echo "Python"
which python
which pip
pip freeze
echo "Python3"
which python3
which pip3
pip3 freeze
python3 -m infra $@
popd
