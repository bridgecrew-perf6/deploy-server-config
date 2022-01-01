#!/usr/bin/env bash

while getopts h: flag
do
    case "${flag}" in
        h) host=${OPTARG};;
    esac
done
[ -z "$host" ] && echo "Usage: $0 -h <host_to_deploy>" && exit 1

set -e
source env/bin/activate
pip install pip --upgrade
pip install -r requirements.txt
fab -f ./config/fabfile.py deploy:host=$host
deactivate

# eof